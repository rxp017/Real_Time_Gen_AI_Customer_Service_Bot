"""Clock-driven escalation, calendar routing, and masked conversation summaries."""

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from core.audit import AuditLogger
from core.business_time import BusinessCalendar
from core.clock import Clock
from core.config import get_config
from core.language import LanguageProcessor
from core.metrics import MetricsCollector
from core.risk import HighRiskDetector
from core.security import mask_pii
from core.sentiment import SentimentClassifier
from core.store import EscalationRepository
from core.tone import TonePresenter


class EscalationRouter:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def route(self, urgent: bool) -> dict[str, Any]:
        cfg = get_config()
        calendar = BusinessCalendar()
        now = self.clock.now().astimezone(calendar.zone)
        if calendar.is_open(now):
            return {"queue": cfg.get("support.queues.business"), "scheduled_for": now.isoformat()}
        if urgent:
            return {"queue": cfg.get("support.queues.urgent_after_hours"), "scheduled_for": now.isoformat()}
        # Outside-hours complaints are scheduled on the next working date, including pre-opening inquiries.
        due = calendar.next_open(now, next_date=True)
        return {"queue": cfg.get("support.queues.normal_after_hours"), "scheduled_for": due.isoformat()}


class EscalationService:
    def __init__(self, repo: EscalationRepository, clock: Clock, audit: AuditLogger,
                 metrics: MetricsCollector, language: LanguageProcessor | None = None) -> None:
        self.repo, self.clock, self.audit, self.metrics = repo, clock, audit, metrics
        self.language = language or LanguageProcessor()
        self.classifier = SentimentClassifier(self.language)
        self.risk = HighRiskDetector(self.language)
        self.router = EscalationRouter(clock)
        self.presenter = TonePresenter()

    def masked(self, message: str) -> str:
        protected = self.language.protect(message, self.language.resources.load())
        text = protected.text
        for entity in protected.entities:
            text = text.replace(entity.token, "[MASKED_NAME]" if entity.kind == "name" else entity.value)
        return mask_pii(text)

    def _record(self, sid: str, generation: int, state: dict[str, Any], records: list[dict[str, Any]],
                kind: str, reason: str, evidence: dict[str, Any]) -> None:
        if kind in state["activated"]:
            return
        record = {"id": uuid4().hex, "session_id": sid, "generation": generation, "episode": state["episode"],
                  "created_at": self.clock.now().isoformat(), "reason": reason,
                  "activated_condition": {"kind": kind, **evidence},
                  "conversation_summary": {"recent_messages": state["history"],
                                           "unresolved_since": state["unresolved_since"]},
                  "urgent": state["urgent"], "status": "OPEN", **self.router.route(state["urgent"])}
        records.append(record)
        state["activated"].append(kind)

    def _timer(self, sid: str, generation: int, state: dict[str, Any], records: list[dict[str, Any]]) -> None:
        if state["unresolved_since"] is None or state["resolved"]:
            return
        elapsed = (self.clock.now() - datetime.fromisoformat(state["unresolved_since"])).total_seconds()
        threshold = float(get_config().get("timings.escalation_timeout_minutes")) * 60
        if elapsed > threshold:
            self._record(sid, generation, state, records, "unresolved_negative", "Negative issue remains unresolved",
                         {"elapsed_seconds": elapsed, "threshold_seconds": threshold,
                          "started_at": state["unresolved_since"]})

    def _recorded(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self.metrics.increment("escalations")
            self.audit.log_warning("escalation_created", "system", record["reason"], record=record)

    def observe(self, sid: str, generation: int, owner: str, message: str,
                history: list[dict[str, Any]]) -> dict[str, Any]:
        cfg = get_config()
        with self.metrics.time_operation("sentiment_latency"), self.repo.issue(sid, generation, owner) as (state, records):
            recent = history if history else state["history"]
            sentiment = self.classifier.classify(message, recent)
            risks = self.risk.detect(message)
            state["history"] = [{"role": m["role"], "content": self.masked(str(m["content"]))}
                                for m in (recent + [{"role": "user", "content": message}])[-int(cfg.get("support.history_messages")):]]
            was_urgent = state["urgent"]
            state["urgent"] = state["urgent"] or sentiment.label == "urgent" or bool(risks and cfg.get("support.high_risk_urgent"))
            now = self.clock.now()
            window = float(cfg.get("support.negative_window_minutes"))
            count = int(cfg.get("support.repeated_negative_count"))
            if window <= 0 or count < 1:
                raise ValueError("Negative count and window must be positive")
            state["negative_events"] = [t for t in state["negative_events"]
                                        if timedelta(0) <= now - datetime.fromisoformat(t) <= timedelta(minutes=window)]
            if sentiment.negative and sentiment.confidence >= float(cfg.get("support.sentiment_threshold")):
                state["resolved"] = False
                state["unresolved_since"] = state["unresolved_since"] or now.isoformat()
                state["negative_events"].append(now.isoformat())
            for risk in risks:
                state["resolved"] = False
                self._record(sid, generation, state, records, "high_risk:" + risk, "High-risk issue: " + risk,
                             {"category": risk, "sentiment_label": sentiment.label})
            if len(state["negative_events"]) >= count:
                self._record(sid, generation, state, records, "repeated_negative", "Repeated negative messages",
                             {"count": len(state["negative_events"]), "required_count": count, "window_minutes": window})
            self._timer(sid, generation, state, records)
            if state["urgent"] and not was_urgent:
                self._upgrade(sid, generation, owner, state["episode"])
        self._recorded(records)
        self.metrics.record_value("sentiment_confidence", sentiment.confidence)
        return {"sentiment": asdict(sentiment), "high_risk": risks,
                "escalations": self.repo.records(sid, owner)}

    def _upgrade(self, sid: str, generation: int, owner: str, episode: int) -> None:
        for record in self.repo.records(sid, owner):
            if record["generation"] == generation and record["episode"] == episode and record["status"] == "OPEN" and not record["urgent"]:
                record.update(urgent=True, **self.router.route(True))
                record["rerouted_at"] = self.clock.now().isoformat()
                self.repo.update_record(record)
                self.audit.log_info("escalation_rerouted", "system", "Urgency changed", record=record)

    def tick(self) -> list[dict[str, Any]]:
        created = []
        for sid, generation, owner in self.repo.issues():
            with self.repo.issue(sid, generation, owner) as (state, records):
                self._timer(sid, generation, state, records)
            self._recorded(records)
            created.extend(records)
        return created

    def resolve(self, sid: str, generation: int, reason: str) -> list[dict[str, Any]]:
        if not reason.strip():
            raise ValueError("Resolution reason is required")
        issue = next((item for item in self.repo.issues() if item[:2] == (sid, generation)), None)
        if issue is None:
            raise ValueError("Unknown issue")
        _, _, owner = issue
        with self.repo.issue(sid, generation, owner) as (state, _):
            episode = state["episode"]
            for record in self.repo.records(sid, owner):
                if record["generation"] == generation and record["episode"] == episode and record["status"] == "OPEN":
                    record.update(status="RESOLVED", resolved_at=self.clock.now().isoformat(), resolution_reason=self.masked(reason))
                    self.repo.update_record(record)
            state.update(episode=episode + 1, negative_events=[], unresolved_since=None,
                         activated=[], urgent=False, resolved=True)
        self.audit.log_info("issue_resolved", "support", self.masked(reason), session_id=sid, generation=generation)
        return self.repo.records(sid, owner)
