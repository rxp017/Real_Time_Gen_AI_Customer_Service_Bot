"""Multilingual turn handling around the existing policy chatbot, without executing intents."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from core.audit import AuditLogger
from core.config import get_config
from core.escalation import EscalationService
from core.language import LanguageProcessor
from core.metrics import MetricsCollector
from core.retrieval import GenerationResult
from core.security import detect_prompt_injection
from core.sentiment import Sentiment
from core.sessions import SessionManager
from core.store import EscalationRepository, TicketRepository
from core.tickets import TicketService


@dataclass
class ConversationResult:
    answer: str
    session_id: str
    language: str
    language_confidence: float
    detected_languages: list[str]
    mixed_language: bool
    requests: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    context: dict[str, Any]
    session_transition: str
    generation: int
    summary: dict[str, Any] | None
    clarification_needed: bool = False
    citations: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = True
    refusal: bool = False
    is_injected: bool = False
    answer_language: str = ""
    sentiment: dict[str, Any] = field(default_factory=dict)
    high_risk: list[str] = field(default_factory=list)
    escalations: list[dict[str, Any]] = field(default_factory=list)
    tone_prefix: str = ""
    display_answer: str = ""
    tickets: list[dict[str, Any]] = field(default_factory=list)
    source_answer: str = ""


class ConversationService:
    def __init__(self, sessions: SessionManager, audit: AuditLogger, metrics: MetricsCollector) -> None:
        self.sessions, self.audit, self.metrics = sessions, audit, metrics
        self.language = LanguageProcessor()
        self.support = EscalationService(EscalationRepository(sessions.repo.db_path), sessions.clock,
                                         audit, metrics, self.language)
        self.tickets = TicketService(TicketRepository(sessions.repo.db_path), sessions.clock, audit, metrics,
                                     self.support.masked)

    def turn(self, question: str, session_id: str | None, owner: str,
             responder: Callable[[str], GenerationResult], unresolved: bool = False) -> ConversationResult:
        cfg = get_config()
        if len(question) > int(cfg.get("conversation.max_message_characters")):
            raise ValueError("Message exceeds configured length limit")
        with self.metrics.time_operation("conversation_latency"), self.sessions.conversation(session_id, owner) as (sid, state, transition):
            support = self.support.observe(sid, state["generation"], owner, question, state["messages"])
            last = state["last_intents"][0] if len(state["last_intents"]) == 1 else None
            analysis = self.language.analyze(question, last)
            detection = analysis.detection
            state["language"] = detection.language
            entities = [{"kind": e.kind, "value": e.value, "usage": e.usage} for e in analysis.protected.entities
                        if e.kind != "citation"]
            prior_context = deepcopy(state["entities"])
            for entity in entities:
                kind, value = entity["kind"], entity["value"]
                old = state["entities"].get(kind)
                if entity["usage"] == "superseded":
                    state["superseded"].append({"kind": kind, "value": value, "reason": "explicit_correction"})
                    continue
                if old is not None and old != value:
                    state["superseded"].append({"kind": kind, "value": old, "reason": "newer_value"})
                state["entities"][kind] = value
            state["superseded"] = state["superseded"][-int(cfg.get("conversation.superseded_limit")):]
            requests = []
            corrected_kinds = {e["kind"] for e in entities if e["usage"] == "superseded"}
            for request in analysis.requests:
                context = deepcopy(prior_context)
                context.update({kind: state["entities"][kind] for kind in corrected_kinds if kind in state["entities"]})
                for entity in analysis.protected.entities:
                    if entity.token in request.text and entity.usage != "superseded" and entity.kind != "citation":
                        context[entity.kind] = entity.value
                requests.append({"intent": request.name, "confidence": request.confidence,
                                 "question": analysis.protected.restore(request.text, False),
                                 "inherited": request.inherited, "context": context})
            needs_clarification = detection.confidence <= 0 or detection.confidence < float(cfg.thresholds["language_confidence"]) or any(
                r.name == "unknown" or r.confidence < float(cfg.thresholds["intent_confidence"]) for r in analysis.requests
            )
            restored_text = analysis.protected.restore(analysis.normalized)
            is_injected = detect_prompt_injection(restored_text)[0]
            citations, answers, unresolved_requests, source_answers = [], [], [], []
            verified, refusal, answer_languages = True, False, []
            if is_injected:
                answers = ["I cannot fulfill this request as it violates security policies."]
            elif needs_clarification:
                answers = [self.language.message(detection.language, "clarification")]
                self.metrics.increment("conversation_clarifications")
            else:
                resources = self.language.resources.load()
                queries = resources[cfg.get("conversation.default_language")].get("canonical_queries", {})
                successful_intents = []
                for request, request_data in zip(analysis.requests, requests, strict=True):
                    if request.name == "correction":
                        correction_values = [e["value"] for e in entities if e["usage"] != "superseded"]
                        answers.append(self.language.message(detection.language, "correction") + " " + ", ".join(correction_values))
                        answer_languages.append(detection.language)
                        continue
                    query = analysis.protected.restore(self.language.retrieval_text(request.text), False)
                    if request.inherited:
                        query = queries.get(request.name, request.name)
                    # Recent entities remain available even after their messages leave the window.
                    context_kinds = resources[cfg.get("conversation.default_language")].get("context_kinds", {}).get(request.name, [])
                    context_values = [request_data["context"][kind] for kind in context_kinds
                                      if kind in request_data["context"]]
                    query += " " + " ".join(v for v in context_values if v not in query)
                    generated = responder(query.strip())
                    source_answers.append(generated.answer)
                    localized, changed = self.language.localize(generated.answer, detection.language)
                    answers.append(localized)
                    answer_languages.append(detection.language if changed or detection.language == cfg.get("conversation.default_language") else cfg.get("conversation.default_language"))
                    citations.extend(c for c in generated.citations if c not in citations)
                    verified = verified and generated.verified
                    refusal = refusal or generated.refusal
                    if generated.refusal or generated.clarification_needed:
                        unresolved_requests.append(request_data)
                    successful_intents.append(request.name)
                if successful_intents:
                    state["last_intents"] = successful_intents
            answer = "\n".join(answers)
            presentation = self.support.presenter.present(answer, Sentiment(**support["sentiment"]))
            self.sessions.append(state, "user", question)
            self.sessions.append(state, "assistant", answer)
            if (support["escalations"] or unresolved or self.tickets.requested_handoff(question)) and not unresolved_requests and not is_injected:
                unresolved_requests = requests
            tickets = self.tickets.unresolved(owner, sid, state["generation"], unresolved_requests,
                                                self.sessions.summarize(state), state["messages"])
            self.metrics.record_value("language_confidence", detection.confidence)
            for request in requests:
                self.metrics.record_value("intent_confidence", request["confidence"])
            self.audit.log_info("conversation_turn", "caller", "Conversation processed",
                                language=detection.language, confidence=detection.confidence,
                                transition=transition, intents=[r["intent"] for r in requests])
            return ConversationResult(answer, sid, detection.language, detection.confidence, detection.languages,
                                      detection.mixed, requests, entities, deepcopy(state["entities"]), transition,
                                      state["generation"], deepcopy(state["summary"]), needs_clarification or is_injected,
                                      citations, verified and not is_injected, refusal, is_injected,
                                      ",".join(sorted(set(answer_languages))) if answer_languages else detection.language,
                                      support["sentiment"], support["high_risk"], support["escalations"],
                                      presentation["tone_prefix"], presentation["display_answer"], tickets,
                                      source_answer="\n".join(source_answers) or answer)
