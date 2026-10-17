"""Chatbot orchestrator application.

Wraps the existing training-project bot and extends it in place with:
1. FastAPI REST API endpoints (/query, /health, /metrics).
2. RBAC authentication via x-api-key.
3. Prompt injection detection and defense.
4. PII masking on incoming inquiries and audit trails.
5. Unified Clock-based timing and operational telemetry metrics.
"""

import asyncio
import hashlib
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from threading import RLock
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.upload_api import UploadBodyLimit, set_upload_service, upload_service
from app.upload_api import router as upload_router
from core.audit import get_audit_logger, set_audit_logger
from core.clock import get_clock
from core.config import get_config
from core.conversation import ConversationService
from core.llm import RealProviderAdapter
from core.metrics import get_metrics, set_metrics
from core.retrieval import PolicyRetrievalEngine
from core.security import (
    authenticate,
    detect_prompt_injection,
    is_authorized,
    mask_pii,
)
from core.sessions import SessionManager
from core.store import (
    AuditLogRepository,
    MetricsRepository,
    SessionRepository,
    SnapshotRepository,
    UploadRepository,
)
from core.updates import UpdateService
from core.upload_processing import UploadProcessor
from core.uploads import UploadService

load_dotenv(override=False)


class QueryRequest(BaseModel):
    """Incoming user query payload."""

    question: str = Field(..., description="The user's query or customer service inquiry.")
    session_id: str | None = Field(default=None, description="Optional conversational session identifier.")
    as_of: str | None = Field(default=None, description="Optional historical timestamp query target.")
    unresolved: bool = Field(default=False, description="Customer explicitly requests a ticket/human handoff.")


class QueryResponse(BaseModel):
    """Outgoing structured chatbot response."""

    answer: str
    role: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    is_injected: bool = False
    verified: bool = True
    session_id: str | None = None
    language: str | None = None
    language_confidence: float | None = None
    detected_languages: list[str] = Field(default_factory=list)
    mixed_language: bool = False
    requests: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    session_transition: str | None = None
    generation: int | None = None
    summary: dict[str, Any] | None = None
    clarification_needed: bool = False
    answer_language: str | None = None
    sentiment: dict[str, Any] = Field(default_factory=dict)
    high_risk: list[str] = Field(default_factory=list)
    escalations: list[dict[str, Any]] = Field(default_factory=list)
    tone_prefix: str = ""
    display_answer: str = ""
    tickets: list[dict[str, Any]] = Field(default_factory=list)
    ticket_questions: list[str] = Field(default_factory=list)


# Optional reference to Task 4 pipeline or baseline chain
_TASK4_ENGINE = None
_UPDATE_SERVICE: UpdateService | None = None
_CONVERSATION_SERVICE: ConversationService | None = None
_CONVERSATION_INIT_LOCK = RLock()


def set_task4_engine(engine: Any) -> None:
    """Inject Task 4 policy and knowledge retrieval engine."""
    global _TASK4_ENGINE
    _TASK4_ENGINE = engine


def set_conversation_service(service: ConversationService | None) -> None:
    global _CONVERSATION_SERVICE
    _CONVERSATION_SERVICE = service


def conversation_service() -> ConversationService:
    global _CONVERSATION_SERVICE
    with _CONVERSATION_INIT_LOCK:
        if _CONVERSATION_SERVICE is None:
            _CONVERSATION_SERVICE = ConversationService(SessionManager(SessionRepository(), get_clock()),
                                                        get_audit_logger(), get_metrics())
    return _CONVERSATION_SERVICE


def set_update_service(service: UpdateService | None) -> None:
    global _UPDATE_SERVICE
    _UPDATE_SERVICE = service
    set_audit_logger(service.audit if service else None)
    set_metrics(service.metrics if service else None)
    if service is not None:
        set_task4_engine(PolicyRetrievalEngine(service.repo, service.llm))


def update_service() -> UpdateService:
    if _UPDATE_SERVICE is None:
        raise HTTPException(status_code=503, detail="Update service is not initialized")
    return _UPDATE_SERVICE


async def maintenance_worker() -> None:
    while True:
        service = update_service()
        def background_tick() -> None:
            operations = [("uploads", lambda: upload_service().purge())]
            if _CONVERSATION_SERVICE is not None:
                operations.extend([("escalations", _CONVERSATION_SERVICE.support.tick),
                                   ("tickets", _CONVERSATION_SERVICE.tickets.tick),
                                   ("sessions", _CONVERSATION_SERVICE.sessions.expire_idle)])
            for name, operation in operations:
                try:
                    operation()
                except Exception as exc:  # noqa: BLE001 - independent workers must survive another domain's outage
                    service.audit.log_error("background_domain_failure", "system", type(exc).__name__, domain=name)
                    service.metrics.increment(f"{name}_worker_failures")
            service.tick()
        running_tick = asyncio.create_task(asyncio.to_thread(background_tick))
        try:
            await asyncio.shield(running_tick)
        except asyncio.CancelledError:
            await running_tick
            raise
        except Exception as exc:  # noqa: BLE001 - keep the worker alive after dependency outages
            service.audit.log_error("scheduler_failure", "system", type(exc).__name__)
            service.metrics.increment("update_failures")
        await asyncio.to_thread(service.clock.sleep, min(float(get_config().get("updates.health_poll_seconds")),
                                                        float(get_config().get("uploads.purge_interval_seconds")),
                                                        float(get_config().get("tickets.poll_seconds"))))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    audit = get_audit_logger()
    clock = get_clock()
    owned = []
    task = None
    owned_uploads = None
    if _TASK4_ENGINE is None:
        db_path = os.getenv("DB_PATH", "data/bot.db")
        repo = SnapshotRepository(db_path)
        audit_repo, metrics_repo = AuditLogRepository(db_path), MetricsRepository(db_path)
        owned = [repo, audit_repo, metrics_repo]
        audit = get_audit_logger(audit_repo)
        metrics = get_metrics(metrics_repo)
        cfg = get_config()
        upload_repo = UploadRepository(db_path)
        owned.append(upload_repo)
        processor = UploadProcessor()
        owned_uploads = UploadService(upload_repo, clock, audit, metrics, processor)
        set_upload_service(owned_uploads)
        owned_uploads.recover()
        provider = RealProviderAdapter()
        if repo.active_info() is None and repo.count() == 0 and provider.api_key and provider.model:
            from core.training import faq_documents

            bootstrap = PolicyRetrievalEngine(repo, provider)
            for document in faq_documents():
                bootstrap.ingest_document(document)
        service = UpdateService(repo, provider, clock, audit, metrics,
                                Path(cfg.get("updates.quarantine")), Path(cfg.get("updates.golden")))
        set_update_service(service)
        session_repo = SessionRepository(db_path)
        owned.append(session_repo)
        set_conversation_service(ConversationService(SessionManager(session_repo, clock), audit, metrics))
        owned.append(conversation_service().support.repo)
        owned.append(conversation_service().tickets.repo)
        inbox = Path(cfg.get("updates.inbox"))
        inbox.mkdir(parents=True, exist_ok=True)
        if repo.load_job() is None:
            key = os.getenv("API_KEY_ADMIN")
            if key:
                service.schedule([], key, discover_inbox=True)
        task = asyncio.create_task(maintenance_worker())
    audit.log_info("app_start", "system", f"Chatbot orchestrator initialized at {clock.now().isoformat()}")
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                audit.log_info("scheduler_stopped", "system", "Maintenance worker stopped")
        audit.log_info("app_stop", "system", "Chatbot orchestrator shut down.")
        if owned:
            if owned_uploads is not None:
                await asyncio.to_thread(owned_uploads.close)
                set_upload_service(None)
            set_conversation_service(None)
            set_update_service(None)
            set_task4_engine(None)
            for repository in owned:
                repository.close()


app = FastAPI(
    title="Customer Service GenAI Chatbot",
    version="1.0.0",
    description="Enterprise Customer Service Chatbot with RBAC, PII masking, and Policy Verification.",
    lifespan=lifespan,
)
app.add_middleware(UploadBodyLimit)
app.include_router(upload_router)


@app.get("/health")
def health_check() -> dict[str, Any]:
    """System health check endpoint using Clock."""
    clock = get_clock()
    cfg = get_config()
    configured = _TASK4_ENGINE is not None
    provider_ready = configured and (not isinstance(_TASK4_ENGINE.llm, RealProviderAdapter)
                                     or bool(_TASK4_ENGINE.llm.api_key and _TASK4_ENGINE.llm.model))
    return {
        "status": "healthy" if provider_ready else "degraded",
        "current_time": clock.now().isoformat(),
        "timezone": cfg.timezone,
    }


@app.get("/metrics")
def metrics_endpoint() -> dict[str, Any]:
    """Operational telemetry endpoint."""
    metrics = get_metrics()
    return metrics.get_summary()


@app.post("/query", response_model=QueryResponse)
def handle_query(
    payload: QueryRequest,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> QueryResponse:
    """Handle incoming user question with security filters and baseline/task4 routing."""
    metrics = get_metrics()
    audit = get_audit_logger()
    metrics.increment("queries_total")

    with metrics.time_operation("query_latency"):
        # 1. RBAC Authentication
        role, _permissions = authenticate(x_api_key)
        if x_api_key is not None and x_api_key not in get_config().api_keys:
            audit.log_security("query_access_denied", role, "Unknown API key")
            raise HTTPException(status_code=403, detail="Unknown API key")
        if not is_authorized(role, "query:public"):
            audit.log_security("query_access_denied", role, "Query permission required")
            raise HTTPException(status_code=403, detail="Query permission required")

        # 2. Prompt Injection Detection on user input
        is_injected, score, matched = detect_prompt_injection(payload.question)
        if is_injected:
            metrics.increment("prompt_injections_detected")
            audit.log_security(
                "prompt_injection_blocked",
                role,
                "Injection detected in query",
                matched=matched,
                score=score,
            )
            if _TASK4_ENGINE is None:
                return QueryResponse(
                    answer="I cannot fulfill this request as it violates security policies.",
                    role=role,
                    is_injected=True,
                    verified=False,
                    session_id=payload.session_id,
                )

        # 3. Log audit event with PII masking
        audit.log_info(
            "user_query",
            role,
            "Received customer-service message",
            characters=len(payload.question),
        )

        # 4. Route query to Task 4 engine if registered, or baseline bot
        if _TASK4_ENGINE is not None:
            try:
                owner = hashlib.sha256((x_api_key or "anonymous").encode("utf-8")).hexdigest()
                def responder(question: str) -> Any:
                    return _TASK4_ENGINE.query(question=question, caller_role=role, as_of=payload.as_of)
                result = conversation_service().turn(payload.question, payload.session_id, owner, responder, payload.unresolved)
            except PermissionError as exc:
                audit.log_security("session_access_denied", role, "Session belongs to another caller")
                raise HTTPException(status_code=403, detail="Session belongs to another caller") from exc
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=mask_pii(str(exc))) from exc
            except Exception as exc:
                audit.log_error("query_provider_failure", role, type(exc).__name__)
                raise HTTPException(status_code=503, detail="Query dependency unavailable") from exc
            return QueryResponse(
                answer=result.answer,
                role=role,
                citations=result.citations,
                is_injected=result.is_injected,
                verified=result.verified,
                session_id=result.session_id,
                language=result.language,
                language_confidence=result.language_confidence,
                detected_languages=result.detected_languages,
                mixed_language=result.mixed_language,
                requests=result.requests,
                entities=result.entities,
                context=result.context,
                session_transition=result.session_transition,
                generation=result.generation,
                summary=result.summary,
                clarification_needed=result.clarification_needed,
                answer_language=result.answer_language,
                sentiment=result.sentiment,
                high_risk=result.high_risk,
                escalations=result.escalations,
                tone_prefix=result.tone_prefix,
                display_answer=result.display_answer,
                tickets=result.tickets,
                ticket_questions=[t["question"] for t in result.tickets if t["question"]],
            )

        # Baseline fallback execution
        safe_question = mask_pii(payload.question)
        try:
            from src.langchain_helper import get_qa_chain
            result = get_qa_chain()(safe_question)
        except Exception as exc:
            audit.log_error("baseline_unavailable", role, type(exc).__name__)
            raise HTTPException(status_code=503, detail="Baseline provider unavailable; configure the policy engine.") from exc
        return QueryResponse(
            answer=result["result"],
            role=role,
            citations=[],
            is_injected=False,
            verified=False,
            session_id=payload.session_id,
        )


def ticket_access(api_key: str | None) -> str:
    role, _ = authenticate(api_key)
    if api_key not in get_config().api_keys or not is_authorized(role, "ticket:manage"):
        get_audit_logger().log_security("ticket_access_denied", role, "Ticket management permission required")
        raise HTTPException(status_code=403, detail="Ticket management permission required")
    return role


class ResolutionRequest(BaseModel):
    generation: int = Field(ge=1)
    reason: str = Field(min_length=1)


class TicketRequest(BaseModel):
    session_id: str = Field(min_length=1)
    fields: dict[str, str] = Field(default_factory=dict)
    draft_id: str | None = None
    severity: str | None = None
    impact: str | None = None


class TicketResolutionRequest(BaseModel):
    reason: str = Field(min_length=1)


def customer_ticket_owner(api_key: str | None, permission: str) -> str:
    role, _ = authenticate(api_key)
    if api_key not in get_config().api_keys or not is_authorized(role, permission):
        get_audit_logger().log_security("ticket_access_denied", role, "Ticket permission required")
        raise HTTPException(status_code=403, detail="Ticket permission required")
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


@app.post("/tickets")
def collect_ticket(payload: TicketRequest, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    owner = customer_ticket_owner(x_api_key, "ticket:create")
    service = conversation_service()
    try:
        state = service.sessions.inspect(payload.session_id, owner)
        if state is None:
            raise ValueError("Session not found; start a conversation first")
        summary = state["summary"] or service.sessions.summarize(state)
        return service.tickets.collect(owner, payload.session_id, state["generation"], payload.fields,
                                       summary, state["messages"], payload.draft_id, payload.severity, payload.impact)
    except PermissionError as exc:
        get_audit_logger().log_security("ticket_access_denied", "caller", "Ticket/session belongs to another caller")
        raise HTTPException(status_code=403, detail="Ticket/session belongs to another caller") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=mask_pii(str(exc))) from exc


@app.get("/tickets")
def list_tickets(x_api_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    owner = customer_ticket_owner(x_api_key, "ticket:view_own")
    role, _ = authenticate(x_api_key)
    return conversation_service().tickets.view(None if is_authorized(role, "ticket:manage") else owner)


@app.post("/tickets/{ticket_id}/close")
def close_ticket(ticket_id: str, payload: TicketResolutionRequest,
                 x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    ticket_access(x_api_key)
    try:
        result = conversation_service().tickets.close_ticket(ticket_id, payload.reason)
        get_audit_logger().log_info("ticket_closed", "support", "Ticket resolved", ticket_id=ticket_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=mask_pii(str(exc))) from exc


@app.get("/escalations")
def escalation_records(x_api_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    ticket_access(x_api_key)
    return conversation_service().support.repo.records()


@app.post("/escalations/{session_id}/resolve")
def resolve_escalation(session_id: str, payload: ResolutionRequest,
                       x_api_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    ticket_access(x_api_key)
    try:
        return conversation_service().support.resolve(session_id, payload.generation, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=mask_pii(str(exc))) from exc


def management_call(operation: str, version: int | None, api_key: str | None) -> Any:
    service = update_service()
    try:
        if operation in {"ingest", "schedule"}:
            inbox = Path(get_config().get("updates.inbox"))
            files = sorted(p for p in inbox.iterdir() if p.is_file()) if inbox.exists() else []
            if operation == "schedule":
                return service.schedule(files, api_key, discover_inbox=True)
            return service.ingest(files, api_key)
        return getattr(service, operation)(version, api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/knowledge/ingest")
def ingest_endpoint(x_api_key: str | None = Header(default=None)) -> Any:
    return management_call("ingest", None, x_api_key)


@app.post("/knowledge/schedule")
def schedule_endpoint(x_api_key: str | None = Header(default=None)) -> Any:
    return management_call("schedule", None, x_api_key)


@app.post("/knowledge/{version}/quality")
def quality_endpoint(version: int, x_api_key: str | None = Header(default=None)) -> Any:
    return management_call("quality_gate", version, x_api_key)


@app.post("/knowledge/{version}/approve")
def approve_endpoint(version: int, x_api_key: str | None = Header(default=None)) -> Any:
    management_call("approve", version, x_api_key)
    return {"version": version, "status": "APPROVED"}


@app.post("/knowledge/{version}/activate")
def activate_endpoint(version: int, x_api_key: str | None = Header(default=None)) -> Any:
    management_call("activate", version, x_api_key)
    return {"active_version": update_service().repo.active_info()["version"]}


@app.post("/knowledge/{version}/rollback")
def rollback_endpoint(version: int, x_api_key: str | None = Header(default=None)) -> Any:
    management_call("rollback", version, x_api_key)
    return {"active_version": update_service().repo.active_info()["version"]}


@app.get("/knowledge")
def view_active_endpoint(x_api_key: str | None = Header(default=None)) -> Any:
    return management_call("view", None, x_api_key)


@app.get("/knowledge/{version}")
def view_endpoint(version: int, x_api_key: str | None = Header(default=None)) -> Any:
    return management_call("view", version, x_api_key)
