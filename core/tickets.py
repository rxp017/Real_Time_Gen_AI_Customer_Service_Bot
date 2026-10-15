"""Owner-isolated ticket collection, deduplication, routing and business SLA events."""

import json
import re
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.audit import AuditLogger
from core.business_time import BusinessCalendar
from core.clock import Clock
from core.config import get_config
from core.metrics import MetricsCollector
from core.priority import priority_score
from core.security import mask_pii
from core.sentiment import SentimentClassifier
from core.store import TicketRepository


class TicketService:
    def __init__(self, repo: TicketRepository, clock: Clock, audit: AuditLogger,
                 metrics: MetricsCollector, masker: Callable[[str], str] = mask_pii) -> None:
        self.repo, self.clock, self.audit, self.metrics, self.masked = repo, clock, audit, metrics, masker
        self.classifier = SentimentClassifier()

    def requested_handoff(self, message: str) -> bool:
        return any(re.search(pattern, message, re.IGNORECASE)
                   for pattern in get_config().get("tickets.unresolved_patterns"))

    def _tokens(self, issue: str) -> set[str]:
        return set(re.findall(r"\w+", issue.casefold())) - set(get_config().get("tickets.similarity_stopwords"))

    def _family(self, issue: str) -> str:
        matches = [name for name, rule in get_config().get("tickets.issue_families").items()
                   if re.search(rule["pattern"], issue, re.IGNORECASE)]
        return matches[0] if len(matches) == 1 else "unmapped:" + " ".join(sorted(self._tokens(issue)))

    def _similar(self, first: str, second: str) -> bool:
        a, b = self._tokens(first), self._tokens(second)
        distinctions = set(get_config().get("tickets.duplicate_distinguishing_words"))
        if a & distinctions != b & distinctions:
            return False
        if {t for t in a if any(c.isdigit() for c in t)} != {t for t in b if any(c.isdigit() for c in t)}:
            return False
        return bool(a and b) and len(a & b) / len(a | b) >= float(get_config().get("tickets.duplicate_similarity"))

    def _event(self, ticket: dict[str, Any], kind: str, reason: str, **detail: Any) -> None:
        if any(e["kind"] == kind for e in ticket["events"]):
            return
        ticket["events"].append({"kind": kind, "at": self.clock.now().isoformat(), "reason": reason, **detail})

    def _refresh(self, ticket: dict[str, Any], records: list[dict[str, Any]], route: bool = True) -> None:
        cfg = get_config()
        cal, now = BusinessCalendar(), self.clock.now()
        created = datetime.fromisoformat(ticket["created_at"])
        elapsed = cal.minutes(created, now)
        target = float(cfg.get("tickets.sla_minutes")[ticket["severity"]])
        if target <= 0:
            raise ValueError("SLA target must be positive")
        ratio = elapsed / target
        ticket["sla"] = {"target_minutes": target, "consumed_minutes": elapsed, "ratio": ratio,
                         "due_at": cal.add_minutes(created, target).isoformat(), "breached": ratio >= 1}
        ticket["priority"] = priority_score(ticket["severity"], ticket["sentiment"]["label"], elapsed,
                                            ticket["impact"], ratio)
        if ratio >= float(cfg.get("tickets.sla_warning_fraction")):
            self._event(ticket, "sla_warning", "SLA warning threshold consumed", ratio=ratio, target_minutes=target)
        if ratio >= 1:
            self._event(ticket, "sla_breach", "Business-time SLA breached", ratio=ratio, target_minutes=target,
                        destination=cfg.get("tickets.escalation_queue"))
            ticket["escalated"] = True
        if route and ticket.get("agent_id") is None:
            self._route(ticket, records, cal)
        if ticket.get("agent_id") is None and elapsed >= float(cfg.get("tickets.queue_escalation_minutes")):
            self._event(ticket, "queue_escalation", "No eligible agent within configured business-time wait",
                        queue_reason=ticket.get("queue_reason"), destination=cfg.get("tickets.escalation_queue"))
            ticket["escalated"] = True

    def _route(self, ticket: dict[str, Any], records: list[dict[str, Any]], cal: BusinessCalendar) -> None:
        cfg, now = get_config(), self.clock.now()
        ticket.update(status="QUEUED", queue_reason=None, scheduled_for=cal.next_open(now).isoformat())
        if not cal.is_open(now):
            ticket["queue_reason"] = "outside_business_hours"
            return
        family = cfg.get("tickets.issue_families").get(ticket["family"])
        required = set(cfg.get("tickets.product_skills").get(ticket["fields"]["product"], []))
        if family:
            required.update(family["skills"])
        ticket["required_skills"] = sorted(required)
        if not required:
            ticket["queue_reason"] = "no_skill_mapping"
            return
        eligible = []
        for agent in cfg.get("tickets.agents"):
            workload = sum(r.get("agent_id") == agent["id"] and r["status"] not in {"CLOSED", "DRAFT", "MERGED"}
                           for r in records)
            if agent["available"] and required <= set(agent["skills"]) and workload < int(agent["capacity"]):
                eligible.append((workload, agent["id"]))
        if eligible:
            workload, agent_id = min(eligible)
            ticket.update(status="ASSIGNED", agent_id=agent_id, queue_reason=None, assigned_workload=workload)
            self._event(ticket, "assigned", "Eligible agent selected by skills, availability and workload", agent_id=agent_id)
        else:
            ticket["queue_reason"] = "no_eligible_agent"

    def collect(self, owner: str, session_id: str, generation: int, fields: dict[str, Any],
                summary: dict[str, Any], history: list[dict[str, Any]], draft_id: str | None = None,
                severity: str | None = None, impact: str | None = None) -> dict[str, Any]:
        cfg = get_config()
        allowed = set(cfg.get("tickets.fields"))
        if set(fields) - allowed:
            raise ValueError("Unknown ticket field")
        if any(not isinstance(v, str) or not v.strip() or len(v) > int(cfg.get("tickets.max_field_characters"))
               for v in fields.values()):
            raise ValueError("Ticket fields must be nonempty bounded strings")
        if severity is not None and severity not in cfg.get("tickets.priority.severity"):
            raise ValueError("Unknown severity")
        if impact is not None and impact not in cfg.get("tickets.priority.impact"):
            raise ValueError("Unknown impact")
        with self.metrics.time_operation("ticket_latency"), self.repo.transaction() as records:
            draft = next((r for r in records if r["id"] == draft_id), None) if draft_id else None
            if draft is None and draft_id is None and fields.get("issue"):
                draft = next((r for r in records if r["status"] == "DRAFT" and r["owner"] == owner
                              and r["session_id"] == session_id and r["generation"] == generation
                              and r["fields"].get("issue") == fields["issue"]
                              and all(r["fields"].get(k) == fields.get(k) for k in ("order", "product"))), None)
            if draft_id and (draft is None or draft["owner"] != owner):
                raise PermissionError("Draft does not belong to caller")
            if draft is not None and (draft["status"] != "DRAFT" or draft["session_id"] != session_id
                                      or draft["generation"] != generation):
                raise ValueError("Draft is not open for this session generation")
            if draft is None:
                draft = {"id": uuid4().hex, "owner": owner, "session_id": session_id, "generation": generation,
                         "status": "DRAFT", "fields": {}, "events": [], "requests": [], "agent_id": None,
                         "created_at": self.clock.now().isoformat(), "escalated": False}
                records.append(draft)
            draft["fields"].update(fields)
            draft["severity"] = severity or draft.get("severity", cfg.get("tickets.default_severity"))
            draft["impact"] = impact or draft.get("impact", cfg.get("tickets.default_impact"))
            draft["handoff_summary"] = self.masked(json.dumps({"summary": summary, "fields": draft["fields"]}, ensure_ascii=False))
            missing = [key for key in cfg.get("tickets.mandatory_fields") if not draft["fields"].get(key)]
            draft["missing_fields"] = missing
            draft["question"] = "Please provide: " + ", ".join(missing) + "." if missing else None
            if missing:
                result = deepcopy(draft)
            else:
                issue = draft["fields"]["issue"]
                draft["sentiment"] = vars(self.classifier.classify(issue, history))
                draft["family"] = self._family(issue)
                candidates = [r for r in records if r is not draft and r["status"] not in {"DRAFT", "CLOSED", "MERGED"}
                              and r["owner"] == owner and all(r["fields"][k] == draft["fields"][k]
                                                              for k in ("customer", "order", "product"))
                              and r["family"] == draft["family"]]
                duplicate = next((r for r in candidates if self._similar(issue, r["fields"]["issue"])), None)
                request = {"session_id": session_id, "generation": generation, "fields": deepcopy(draft["fields"]),
                           "at": self.clock.now().isoformat()}
                if duplicate:
                    duplicate["requests"].append(request)
                    for key in ("severity", "impact"):
                        scale = cfg.get(f"tickets.priority.{key}")
                        duplicate[key] = max((duplicate[key], draft[key]), key=lambda value: scale[value])
                    sentiment_scale = cfg.get("tickets.priority.sentiment")
                    duplicate["sentiment"] = max((duplicate["sentiment"], draft["sentiment"]),
                                                  key=lambda value: sentiment_scale[value["label"]])
                    duplicate["handoff_summary"] = self.masked(duplicate["handoff_summary"] + "\n" + draft["handoff_summary"])
                    self._event(duplicate, "duplicate_merged", "Same customer, order and similar issue")
                    draft.update(status="MERGED", merged_into=duplicate["id"])
                    self._refresh(duplicate, records)
                    result = deepcopy(duplicate)
                else:
                    draft["group_id"] = candidates[0]["group_id"] if candidates else uuid4().hex
                    draft["requests"].append(request)
                    # SLA starts when mandatory information is complete, not during collection.
                    draft["created_at"] = self.clock.now().isoformat()
                    self._refresh(draft, records)
                    result = deepcopy(draft)
        self.audit.log_info("ticket_collected", "caller", "Ticket collection persisted", ticket_id=result["id"], status=result["status"])
        self.metrics.increment("ticket_collections")
        return result

    def unresolved(self, owner: str, sid: str, generation: int, requests: list[dict[str, Any]],
                   summary: dict[str, Any], history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for request in requests:
            if request["intent"] == "correction":
                continue
            fields = {"issue": request["question"]}
            context = request["context"]
            for source, target in (("order_id", "order"), ("product_code", "product")):
                if context.get(source):
                    fields[target] = context[source]
            results.append(self.collect(owner, sid, generation, fields, summary, history))
        return results

    def tick(self) -> None:
        with self.repo.transaction() as records:
            open_tickets = [r for r in records if r["status"] in {"QUEUED", "ASSIGNED"}]
            # Recompute before routing so a runtime SLA change affects queue ordering immediately.
            for ticket in open_tickets:
                self._refresh(ticket, records, route=False)
            for ticket in sorted(open_tickets, key=lambda r: (-r["priority"]["score"], r["created_at"], r["id"])):
                if ticket.get("agent_id") is None:
                    self._route(ticket, records, BusinessCalendar())

    def view(self, owner: str | None = None) -> list[dict[str, Any]]:
        return [r for r in self.repo.records() if owner is None or r["owner"] == owner]

    def close_ticket(self, ticket_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("Resolution reason required")
        with self.repo.transaction() as records:
            ticket = next((r for r in records if r["id"] == ticket_id and r["status"] in {"QUEUED", "ASSIGNED"}), None)
            if ticket is None:
                raise ValueError("Open ticket not found")
            ticket.update(status="CLOSED", resolved_at=self.clock.now().isoformat(), resolution=self.masked(reason))
            self._event(ticket, "closed", self.masked(reason))
            return deepcopy(ticket)
