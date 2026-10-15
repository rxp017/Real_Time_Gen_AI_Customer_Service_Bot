"""Durable upload jobs, Clock-bounded inline waiting, delivery, and byte deletion."""

import hashlib
import re
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from core.audit import AuditLogger
from core.clock import Clock
from core.config import get_config
from core.metrics import MetricsCollector
from core.store import UploadRepository
from core.upload_gate import UploadGate, UploadRejected
from core.upload_processing import UploadProcessor


class UploadService:
    def __init__(self, repo: UploadRepository, clock: Clock, audit: AuditLogger, metrics: MetricsCollector,
                 processor: UploadProcessor | None = None, directory: Path | None = None) -> None:
        self.repo, self.clock, self.audit, self.metrics = repo, clock, audit, metrics
        self.processor = processor or UploadProcessor()
        self.gate = UploadGate(audit)
        self.root = (directory or Path(get_config().get("uploads.directory"))).resolve()
        self.root.relative_to(Path.cwd().resolve())
        self.root.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=int(get_config().get("uploads.workers")), thread_name_prefix="upload")
        self._futures: dict[str, Future[Any]] = {}
        self._lock = RLock()

    def close(self) -> None:
        self.executor.shutdown(wait=True, cancel_futures=True)

    def submit(self, data: bytes, filename: str, mime: str, owner: str, message: str,
               purpose: str = "invoice", language: str | None = None) -> dict[str, Any]:
        cfg = get_config()
        language = language or cfg.get("uploads.ocr.default_language")
        if purpose not in {"invoice", "product"} or language not in cfg.get("uploads.ocr.languages"):
            raise ValueError("Invalid upload purpose or OCR language")
        if len(message) > int(cfg.get("conversation.max_message_characters")):
            raise ValueError("Customer message too long")
        start = self.clock.monotonic()
        limit, poll = float(cfg.get("uploads.inline_seconds")), float(cfg.get("uploads.poll_seconds"))
        if not 0 <= limit <= 30 or poll <= 0 or float(cfg.get("uploads.retention_hours")) <= 0:
            raise ValueError("Invalid inline budget, polling, or retention configuration")
        gated = self.gate.validate(data, filename, mime)
        job_id = uuid4().hex
        path = self.root / (job_id + ".bin")
        now = self.clock.now()
        try:
            path.write_bytes(data)
            self.repo.create_upload({"id": job_id, "owner": owner, "created_at": now.isoformat(),
                                     "expires_at": (now + timedelta(hours=float(cfg.get("uploads.retention_hours")))).isoformat(),
                                     "storage_path": str(path), "payload": {"gated": {"mime": gated.mime, "width": gated.width, "height": gated.height},
                                                                             "sha256": hashlib.sha256(data).hexdigest(),
                                                                             "message": message, "purpose": purpose, "language": language}},
                                    int(cfg.get("uploads.max_pending_jobs")))
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        future = self._dispatch(job_id)
        while not future.done():
            if self.clock.monotonic() - start >= limit:
                self.repo.notify_background(job_id, self.clock.now().isoformat())
                self.metrics.increment("uploads_background")
                return {**self.get(job_id, owner), "background": True}
            self.clock.sleep(poll)
        return {**self.get(job_id, owner), "background": False}

    def _dispatch(self, job_id: str) -> Future[Any]:
        with self._lock:
            future = self.executor.submit(self._run, job_id)
            self._futures[job_id] = future
            future.add_done_callback(lambda _: self._forget(job_id))
        return future

    def _forget(self, job_id: str) -> None:
        with self._lock:
            self._futures.pop(job_id, None)

    def _path(self, job: dict[str, Any]) -> Path:
        path = Path(job["storage_path"]).resolve()
        path.relative_to(Path.cwd().resolve())
        if not re.fullmatch(r"[0-9a-f]{32}", job["id"]) or path.name != job["id"] + ".bin":
            raise RuntimeError("Unsafe stored upload path")
        return path

    def _run(self, job_id: str) -> None:
        if not self.repo.claim_upload(job_id):
            return
        start = self.clock.monotonic()
        try:
            job = self.repo.get_upload(job_id)
            if self.clock.now() >= datetime.fromisoformat(job["expires_at"]):
                self.purge()
                return
            payload = job["payload"]
            data = self._path(job).read_bytes()
            if hashlib.sha256(data).hexdigest() != payload["sha256"]:
                raise UploadRejected("stored_content_changed")
            mime = payload["gated"]["mime"]
            suffix = {"image/png": ".png", "image/jpeg": ".jpg", "application/pdf": ".pdf"}[mime]
            gated = self.gate.validate(data, job_id + suffix, mime)
            result = self.processor.process(data, gated, payload["message"], payload["purpose"], payload["language"])
            if self.clock.now() >= datetime.fromisoformat(job["expires_at"]):
                self.purge()
                return
            if self.repo.finish_upload(job_id, "done", result, self.clock.now().isoformat()):
                self.audit.log_info("upload_completed", "caller", "Upload processed", status=result["status"], job_id=job_id)
                self.metrics.increment("uploads_done")
        except Exception as exc:  # noqa: BLE001 - durable failed status, no raw file text or parser errors in logs
            reason = exc.reason if isinstance(exc, UploadRejected) else type(exc).__name__
            self.audit.log_security("upload_processing_failed", "caller", "Upload processing failed", reason=reason, job_id=job_id)
            self.metrics.increment("uploads_failed")
            self.repo.finish_upload(job_id, "failed", {"status": "rejected" if isinstance(exc, UploadRejected) else "failed",
                                                       "reason": reason, "message": "File could not be processed safely."}, self.clock.now().isoformat())
        finally:
            self.metrics.record_latency("upload_processing", (self.clock.monotonic() - start) * 1000)

    def get(self, job_id: str, owner: str) -> dict[str, Any]:
        self.purge()
        job = self.repo.get_upload(job_id, owner)
        return {key: job[key] for key in ("id", "status", "created_at", "expires_at", "result", "notifications", "expired")}

    def recover(self) -> int:
        self.purge()
        recovered = 0
        for job in self.repo.uploads():
            if not job["expired"] and job["status"] in {"queued", "running"}:
                self.repo.requeue_upload(job["id"])
                self._dispatch(job["id"])
                recovered += 1
        return recovered

    def purge(self) -> int:
        removed = 0
        with self._lock:
            for job in self.repo.uploads():
                if job["expired"] or self.clock.now() < datetime.fromisoformat(job["expires_at"]):
                    continue
                self._path(job).unlink(missing_ok=True)
                self.repo.expire_upload(job["id"], self.clock.now().isoformat())
                self.audit.log_info("upload_purged", "system", "Expired upload bytes deleted", job_id=job["id"])
                self.metrics.increment("uploads_purged")
                removed += 1
        return removed
