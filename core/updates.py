"""Controlled RAG updates: evaluation, approval, timed activation, and rollback."""

import json
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from core.audit import AuditLogger
from core.clock import Clock
from core.config import get_config
from core.embeddings import Embedder
from core.ingestion import InvalidFile, quarantine, read_policy
from core.llm import LLMClient
from core.metrics import MetricsCollector
from core.retrieval import PolicyRetrievalEngine
from core.security import authenticate, is_authorized
from core.store import Document, SnapshotRepository, SnapshotView


class UpdateService:
    def __init__(self, repo: SnapshotRepository, llm: LLMClient, clock: Clock,
                 audit: AuditLogger, metrics: MetricsCollector, quarantine_dir: Path,
                 golden_dir: Path, embedder: Embedder | None = None) -> None:
        self.repo, self.llm, self.clock = repo, llm, clock
        self.audit, self.metrics = audit, metrics
        self.quarantine_dir, self.golden_dir = quarantine_dir, golden_dir
        self.embedder = embedder or (llm if getattr(llm, "supports_embeddings", False) else None)
        self.repo.ensure_active()
        job = self.repo.load_job()
        if job and job["status"] == "RUNNING":
            job["status"] = "RETRY"
            self.repo.save_job(job)
            self.audit.log_warning("update_recovered", "system", "Interrupted job resumed")

    def authorize(self, api_key: str | None, operation: str) -> str:
        role, _ = authenticate(api_key)
        # Unknown keys must not inherit public permissions on management endpoints.
        if api_key not in get_config().api_keys or not is_authorized(role, f"knowledge:{operation}"):
            self.audit.log_security("update_access_denied", role, f"Denied {operation}")
            self.metrics.increment("update_unauthorized")
            raise PermissionError(f"Permission required: knowledge:{operation}")
        return role

    def ingest(self, files: list[Path], api_key: str | None) -> dict[str, Any]:
        role = self.authorize(api_key, "ingest")
        with self.repo.lock, self.metrics.time_operation("update_ingest_latency"):
            return self._ingest(files, role)

    def _ingest(self, files: list[Path], role: str) -> dict[str, Any]:
        active = int(self.repo.active_info()["version"])
        baseline = self.repo.snapshot(active)
        docs = {d["doc_id"]: Document(**d) for d in baseline["documents"]}
        manifest = dict(baseline["manifest"])
        hashes = {v["hash"]: name for name, v in manifest.items()}
        processed, skipped = [], []
        rejected: list[dict[str, str]] = []
        for path in sorted(files):
            name = str(path.resolve())
            try:
                data, digest = read_policy(path)
                old = manifest.get(name)
                if old and old["doc_id"] != data["doc_id"]:
                    raise InvalidFile("missing metadata")
            except InvalidFile as exc:
                location = quarantine(path, self.quarantine_dir, exc.reason)
                rejected.append({"reason": exc.reason, "location": str(location)})
                self.audit.log_warning("document_quarantined", role, "Invalid policy file",
                                       filename=path.name, reason=exc.reason)
                self.metrics.increment("update_validation_failures")
                continue
            if old and old["hash"] == digest:
                # A model change refreshes vectors even when source bytes are unchanged.
                PolicyRetrievalEngine(self.repo, self.llm, embedder=self.embedder).prepare_embedding(docs[data["doc_id"]])
                skipped.append({"file": path.name, "reason": "unchanged"})
                self.audit.log_info("document_unchanged", role, "Unchanged file skipped", filename=path.name)
                continue
            if digest in hashes and hashes[digest] != name:
                skipped.append({"file": path.name, "reason": "duplicate"})
                self.audit.log_info("document_duplicate", role, "Duplicate file skipped", filename=path.name)
                self.metrics.increment("update_duplicates")
                continue
            previous = docs.get(data["doc_id"])
            if previous:
                data["version"] = max(data["version"], previous.version + 1)
            document = Document(**data)
            PolicyRetrievalEngine(self.repo, self.llm, embedder=self.embedder).prepare_embedding(document)
            docs[data["doc_id"]] = document
            if old:
                hashes.pop(old["hash"], None)
            manifest[name] = {"hash": digest, "doc_id": data["doc_id"], "version": data["version"]}
            hashes[digest] = name
            processed.append(path.name)
        candidate = self.repo.create_snapshot(list(docs.values()), manifest) if processed else None
        if candidate is not None:
            self.repo.set_state(candidate, "CANDIDATE", {"base_version": active})
        self.audit.log_info("ingestion_complete", role, "Policy ingestion finished", candidate=candidate,
                            processed=len(processed), quarantined=len(rejected), skipped=len(skipped))
        return {"version": candidate, "base_version": active, "processed": processed,
                "skipped": skipped, "quarantined": rejected}

    @staticmethod
    def answer_text(answer: str) -> str:
        return " ".join(re.sub(r"\[[^\]]*\]", "", answer).split()).rstrip(".?!").casefold()

    def evaluate(self, version: int) -> dict[str, Any]:
        cases: list[dict[str, Any]] = []
        for path in sorted(self.golden_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            cases.extend(data if isinstance(data, list) else [data])
        if not cases:
            raise ValueError("Golden Q&A set is empty")
        engine = PolicyRetrievalEngine(SnapshotView(self.repo, version), self.llm, embedder=self.embedder)
        outcomes = []
        for case in cases:
            question, role = case["question"], case.get("role", "public")
            result = engine.query(question, role, case.get("as_of"))
            if case.get("expect_refusal", False):
                correct = result.refusal and not result.is_injected
                grounded = correct and not result.citations and result.verified
            else:
                correct = (not result.refusal and not result.clarification_needed
                           and self.answer_text(result.answer) in
                           [self.answer_text(a) for a in case["answers"]])
                allowed = {(r.document.doc_id, r.document.version, r.document.section): r.document
                           for r in engine.retrieve(question, role, case.get("as_of"))}
                cited = [(c["doc_id"], c["version"], c["section"]) for c in result.citations]
                grounded = (not result.refusal and not result.clarification_needed and result.verified
                            and bool(cited) and all(c in allowed for c in cited))
                for sentence in re.split(r"(?<=[.!?])\s+(?=[^\[])", result.answer):
                    if grounded:
                        grounded = any(engine.verify_claim(sentence, allowed[c].content) for c in cited)
            outcomes.append({"id": case["id"], "accuracy": int(correct), "grounding": int(grounded)})
            if result.refusal or result.clarification_needed:
                self.metrics.increment("update_escalations")
        return {"accuracy": sum(r["accuracy"] for r in outcomes) / len(cases),
                "grounding": sum(r["grounding"] for r in outcomes) / len(cases),
                "total": len(cases), "cases": outcomes}

    def quality_gate(self, version: int, api_key: str | None) -> dict[str, Any]:
        role = self.authorize(api_key, "approve")
        return self._quality_gate(version, role)

    def _quality_gate(self, version: int, role: str) -> dict[str, Any]:
        with self.repo.lock, self.metrics.time_operation("update_quality_latency"):
            candidate = self.repo.snapshot(version)
            if candidate["status"] != "CANDIDATE":
                raise ValueError("Quality gate requires a CANDIDATE snapshot")
            active = int(self.repo.active_info()["version"])
            if candidate["report"]["base_version"] != active:
                self.repo.set_state(version, "STALE")
                raise ValueError("ACTIVE changed since ingestion")
            try:
                baseline, measured = self.evaluate(active), self.evaluate(version)
            except Exception as exc:
                self.repo.set_state(version, "FAILED", {"reason": type(exc).__name__})
                self.metrics.increment("update_failures")
                self.audit.log_error("quality_service_failure", role, type(exc).__name__, version=version)
                raise
            tolerance = float(get_config().get("updates.quality_tolerance"))
            if not 0 <= tolerance <= 1:
                raise ValueError("Quality tolerance must be between 0 and 1")
            accepted = all(measured[k] + tolerance >= baseline[k] for k in ("accuracy", "grounding"))
            report = {"base_version": active, "active": baseline, "candidate": measured,
                      "tolerance": tolerance, "accepted": accepted}
            self.repo.set_state(version, "READY" if accepted else "REJECTED", report)
            self.metrics.record_value("update_confidence", measured["grounding"])
            if not accepted:
                self.metrics.increment("update_failures")
            self.audit.log_info("quality_gate", role, "Measured golden Q&A results", version=version, report=report)
            return report

    def approve(self, version: int, api_key: str | None) -> None:
        role = self.authorize(api_key, "approve")
        with self.repo.lock:
            snapshot = self.repo.snapshot(version)
            if snapshot["status"] != "READY" or not snapshot["report"].get("accepted"):
                raise ValueError("Only quality-gated READY snapshots can be approved")
            if snapshot["report"]["base_version"] != self.repo.active_info()["version"]:
                raise ValueError("ACTIVE changed; candidate needs reevaluation")
            self.repo.set_state(version, "APPROVED")
            self.audit.log_info("update_approved", role, "Candidate held for maintenance window", version=version)

    def inside_window(self) -> bool:
        cfg = get_config()
        now = self.clock.now().astimezone(ZoneInfo(cfg.timezone))
        window = cfg.get("timings.maintenance_window")
        start, end = time.fromisoformat(window["start"]), time.fromisoformat(window["end"])
        days = window.get("days", [window.get("day", "Sunday")])
        if start < end:
            return now.strftime("%A") in days and start <= now.time() < end
        return ((now.strftime("%A") in days and now.time() >= start)
                or ((now - timedelta(days=1)).strftime("%A") in days and now.time() < end))

    def activate(self, version: int, api_key: str | None) -> None:
        role = self.authorize(api_key, "activate")
        self._activate(version, role)

    def _activate(self, version: int, role: str) -> None:
        with self.repo.lock, self.metrics.time_operation("update_activation_latency"):
            if not self.inside_window():
                self.audit.log_warning("activation_held", role, "Outside maintenance window", version=version)
                raise ValueError("Activation blocked outside maintenance window")
            snapshot = self.repo.snapshot(version)
            if snapshot["status"] != "APPROVED":
                raise ValueError("Activation requires an APPROVED candidate")
            self.repo.swap_active(version, snapshot["report"]["base_version"])
            self.repo.set_state(version, "ACTIVATED")
            self.audit.log_info("update_activated", role, "ACTIVE pointer changed", version=version)
            self.check_health()

    def check_health(self) -> None:
        with self.repo.lock:
            info = self.repo.active_info()
            if not info or not info["monitored"]:
                return
            elapsed = self.clock.now() - datetime.fromisoformat(info["activated_at"])
            window = timedelta(minutes=float(get_config().get("updates.health_window_minutes")))
            if elapsed > window:
                self.repo.finish_monitoring()
                return
            version = int(info["version"])
            reason = "health_dependency_failure"
            try:
                scores = self.evaluate(version)
                expected = self.repo.snapshot(version)["report"]["candidate"]
                if any(scores[k] < expected[k] for k in ("accuracy", "grounding")):
                    reason = "health_quality_regression"
                    raise RuntimeError("Post-activation golden health regression")
            except Exception as exc:
                previous = info["previous_version"]
                if previous is None:
                    raise RuntimeError("No previous snapshot available for rollback") from exc
                self.repo.swap_active(int(previous), version, monitored=False)
                report = self.repo.snapshot(version)["report"]
                report["rollback"] = {"reason": reason, "error": type(exc).__name__,
                                      "at": self.clock.now().isoformat(), "restored_version": previous}
                self.repo.set_state(version, "ROLLED_BACK", report)
                self.metrics.increment("update_failures")
                self.metrics.increment("update_escalations")
                self.audit.log_error("auto_rollback", "system", reason,
                                     failed_version=version, restored_version=previous)
                self.audit.log_error("update_alert", "system", "Activation health failure; rolled back")

    def rollback(self, version: int, api_key: str | None) -> None:
        role = self.authorize(api_key, "rollback")
        with self.repo.lock:
            snapshot = self.repo.snapshot(version)
            if snapshot["status"] not in {"READY", "ACTIVATED", "ROLLED_BACK"}:
                raise ValueError("Cannot roll back to a rejected or unevaluated snapshot")
            previous = int(self.repo.active_info()["version"])
            self.repo.swap_active(version, previous, monitored=False)
            self.audit.log_info("manual_rollback", role, "ACTIVE pointer restored", version=version)

    def view(self, version: int | None, api_key: str | None) -> dict[str, Any]:
        role = self.authorize(api_key, "view")
        version = int(self.repo.active_info()["version"]) if version is None else version
        snapshot = self.repo.snapshot(version)
        self.audit.log_info("update_view", role, "Snapshot status viewed", version=version)
        # Management view exposes metadata and reports, never restricted document contents.
        return {k: snapshot[k] for k in ("version", "status", "report")}

    def schedule(self, files: list[Path], api_key: str | None, discover_inbox: bool = False) -> dict[str, Any]:
        role = self.authorize(api_key, "ingest")
        with self.repo.lock:
            old = self.repo.load_job()
            if old and old["status"] in {"WAITING", "RETRY", "RUNNING"}:
                raise ValueError("An update job is already pending")
            cfg = get_config()
            now = self.clock.now().astimezone(ZoneInfo(cfg.timezone))
            due = datetime.combine(now.date(), time.fromisoformat(cfg.get("updates.run_time")), now.tzinfo)
            if due < now:
                due += timedelta(days=1)
            job = {"files": [str(p.resolve()) for p in files], "role": role, "attempt": 0,
                   "due": due.isoformat(), "origin": due.isoformat(), "status": "WAITING",
                   "discover_inbox": discover_inbox}
            self.repo.save_job(job)
            self.audit.log_info("update_scheduled", role, "Daily update scheduled", due=job["due"])
            return job

    def tick(self) -> dict[str, Any] | None:
        """One scheduler/health poll. Caller owns the loop; no hidden wall-clock sleeps."""
        with self.repo.lock:
            self.check_health()
            cfg = get_config()
            system_role = cfg.get("updates.scheduler_role")
            approved = self.repo.conn.execute("SELECT version FROM snapshot_states WHERE status='APPROVED'").fetchall()
            if self.inside_window() and is_authorized(system_role, "knowledge:activate"):
                for row in approved:
                    snapshot = self.repo.snapshot(row[0])
                    if snapshot["report"]["base_version"] != self.repo.active_info()["version"]:
                        self.repo.set_state(row[0], "STALE")
                        self.audit.log_warning("activation_stale", system_role, "Candidate baseline changed", version=row[0])
                    else:
                        self._activate(row[0], system_role)
            job = self.repo.load_job()
            if job and job["status"] not in {"WAITING", "RETRY", "RUNNING"}:
                now = self.clock.now().astimezone(ZoneInfo(cfg.timezone))
                if now.date() > datetime.fromisoformat(job["origin"]).date():
                    due = datetime.combine(now.date(), time.fromisoformat(cfg.get("updates.run_time")), now.tzinfo)
                    job.update(status="WAITING", attempt=0, due=due.isoformat(), origin=due.isoformat(),
                               discover_inbox=job.get("discover_inbox", False))
                    self.repo.save_job(job)
            if not job or job["status"] not in {"WAITING", "RETRY"} or self.clock.now() < datetime.fromisoformat(job["due"]):
                return job
            job["status"] = "RUNNING"
            self.repo.save_job(job)
            try:
                if not is_authorized(job["role"], "knowledge:ingest"):
                    raise PermissionError("Scheduled ingest role no longer authorized")
                with self.metrics.time_operation("update_scheduled_latency"):
                    if job.get("discover_inbox"):
                        inbox = Path(cfg.get("updates.inbox"))
                        files = [p for p in sorted(inbox.glob("*")) if p.is_file()]
                    else:
                        files = [Path(p) for p in job["files"]]
                    result = self._ingest(files, job["role"])
                    if result["quarantined"]:
                        raise ValueError("Scheduled update contains quarantined files")
                    version = result["version"]
                    if version is not None:
                        if not is_authorized(system_role, "knowledge:approve"):
                            raise PermissionError("Scheduler cannot evaluate candidates")
                        report = self._quality_gate(version, system_role)
                        if not report["accepted"]:
                            raise ValueError("Quality gate rejected candidate")
                    job.update(status="AWAITING_APPROVAL" if version else "UNCHANGED", version=version)
            except Exception as exc:
                job["last_error"] = type(exc).__name__
                self.metrics.increment("update_failures")
                self.audit.log_error("scheduled_update_failure", job["role"], type(exc).__name__, attempt=job["attempt"])
                retries = cfg.get("updates.retry_offsets_minutes")
                if retries != [15, 30, 60]:
                    raise ValueError("Exactly three retry offsets [15,30,60] are required") from exc
                if job["attempt"] < len(retries):
                    if job["attempt"] == 0:
                        job["origin"] = self.clock.now().isoformat()
                    job["due"] = (datetime.fromisoformat(job["origin"]) +
                                  timedelta(minutes=retries[job["attempt"]])).isoformat()
                    job["attempt"] += 1
                    job["status"] = "RETRY"
                else:
                    job["status"] = "FAILED"
                    self.metrics.increment("update_escalations")
                    self.audit.log_error("update_alert", "system", "Update FAILED after exactly three retries")
            self.repo.save_job(job)
            return job
