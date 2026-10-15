"""Task 3 acceptance and failure cases use real SQLite, FakeClock and shared layers."""

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.chatbot import app, set_conversation_service, set_task4_engine
from core.audit import AuditLogger
from core.business_time import BusinessCalendar
from core.clock import FakeClock, set_global_clock
from core.config import get_config_manager
from core.conversation import ConversationService
from core.llm import FakeLLM
from core.metrics import MetricsCollector
from core.priority import priority_score
from core.retrieval import PolicyRetrievalEngine
from core.sessions import SessionManager
from core.store import (
    AuditLogRepository,
    DocumentRepository,
    SessionRepository,
    TicketRepository,
)
from core.tickets import TicketService


@pytest.fixture
def tickets(tmp_path: Path):
    clock = FakeClock("2026-10-16T09:00:00+05:30")
    set_global_clock(clock)
    audit = AuditLogger(AuditLogRepository(str(tmp_path / "audit.db")))
    service = TicketService(TicketRepository(str(tmp_path / "tickets.db")), clock, audit, MetricsCollector())
    yield service, clock
    service.repo.close()
    audit.repo.close()


def fields(issue: str = "delivery is late") -> dict[str, str]:
    return {"customer": "customer-17", "order": "ORD-4512", "product": "PRD-007", "issue": issue,
            "evidence": "Customer reports an overdue parcel", "contact": "alice@example.com"}


def create(tickets, issue: str = "delivery is late", **kwargs):
    service, _ = tickets
    return service.collect("owner", "session", 1, fields(issue), {"last_user_request": issue}, [], **kwargs)


def agent(agent_id: str, skills: list[str], available: bool = True, capacity: int = 3):
    return {"id": agent_id, "skills": skills, "available": available, "capacity": capacity}


def test_duplicate_ticket_merged(tickets) -> None:
    service, _ = tickets
    first = create(tickets)
    duplicate = create(tickets, "please my delivery is late")
    assert duplicate["id"] == first["id"] and len(duplicate["requests"]) == 2
    assert len([r for r in service.view() if r["status"] == "QUEUED"]) == 1
    assert any(e["kind"] == "duplicate_merged" for e in duplicate["events"])


def test_related_grouped_unrelated_separate(tickets) -> None:
    a = create(tickets, "delivery is late")
    b = create(tickets, "parcel arrived with missing tracking label")
    c = create(tickets, "account password reset fails")
    assert len({a["id"], b["id"], c["id"]}) == 3
    assert a["group_id"] == b["group_id"] != c["group_id"]
    assert a["session_id"] == b["session_id"] == c["session_id"]


def test_missing_mandatory_requested(tickets) -> None:
    service, clock = tickets
    draft = service.collect("owner", "session", 1, {"issue": "delivery late"}, {}, [])
    assert draft["status"] == "DRAFT"
    assert set(draft["missing_fields"]) == {"customer", "order", "product", "evidence", "contact"}
    assert all(k in draft["question"] for k in draft["missing_fields"])
    assert "sla" not in draft and "customer" not in draft["fields"]
    clock.advance(hours=3)
    final = service.collect("owner", "session", 1, fields(), {}, [], draft["id"])
    assert final["id"] == draft["id"] and final["status"] == "QUEUED"
    assert final["sla"]["consumed_minutes"] == 0


def test_priority_formula() -> None:
    score = priority_score("high", "negative", 240, "team", 0.75)
    assert score["score"] == 65.25
    assert score["components"] == {"severity": 0.75, "sentiment": 0.6, "waiting": 0.5, "impact": 0.6, "sla": 0.75}
    get_config_manager().update_runtime_override("tickets.priority.weights", {"severity": 1, "sentiment": 0, "waiting": 0, "impact": 0, "sla": 0})
    assert priority_score("high", "positive", 99999, "individual", 100)["score"] == 75
    assert priority_score("low", "positive", -20, "individual", -1)["components"]["waiting"] == 0


def test_routing_skills_workload(tickets) -> None:
    get_config_manager().update_runtime_override("tickets.agents", [agent("A", ["delivery"]), agent("B", ["delivery"]),
                                                                  agent("C", ["billing"]), agent("D", ["delivery"], False)])
    a = create(tickets)
    b = create(tickets, "parcel tracking unavailable")
    assert (a["agent_id"], b["agent_id"]) == ("A", "B")
    assert a["required_skills"] == ["delivery"]
    get_config_manager().update_runtime_override("tickets.product_skills", {"PRD-007": ["hardware"]})
    c = create(tickets, "shipping label torn")
    assert c["status"] == "QUEUED" and c["queue_reason"] == "no_eligible_agent"


def test_team_unavailable_queued(tickets) -> None:
    service, clock = tickets
    get_config_manager().update_runtime_override("tickets.agents", [agent("A", ["delivery"], False)])
    ticket = create(tickets)
    assert ticket["status"] == "QUEUED" and ticket["queue_reason"] == "no_eligible_agent"
    clock.advance(minutes=60)
    service.tick()
    ticket = service.view()[0]
    assert ticket["escalated"] and any(e["kind"] == "queue_escalation" for e in ticket["events"])
    get_config_manager().update_runtime_override("tickets.agents", [agent("A", ["delivery"])])
    service.tick()
    assert service.view()[0]["agent_id"] == "A"


def test_after_hours_request(tickets) -> None:
    service, clock = tickets
    clock.set("2026-10-16T18:00:00+05:30")
    get_config_manager().update_runtime_override("holidays", ["2026-10-19"])
    get_config_manager().update_runtime_override("tickets.agents", [agent("A", ["delivery"])])
    ticket = create(tickets)
    assert ticket["queue_reason"] == "outside_business_hours" and ticket["agent_id"] is None
    assert ticket["scheduled_for"] == "2026-10-20T09:00:00+05:30"
    clock.set("2026-10-20T09:00:00+05:30")
    service.tick()
    assert service.view()[0]["sla"]["consumed_minutes"] == 0
    assert service.view()[0]["agent_id"] == "A"


def test_sla_excludes_weekends_and_holidays(tickets) -> None:
    service, clock = tickets
    get_config_manager().update_runtime_override("holidays", ["2026-10-19"])
    clock.set("2026-10-16T17:30:00+05:30")
    ticket = create(tickets)
    assert ticket["sla"]["due_at"] == "2026-10-20T12:30:00+05:30"
    clock.set("2026-10-20T09:30:00+05:30")
    service.tick()
    assert service.view()[0]["sla"]["consumed_minutes"] == 60


def test_sla_75_percent_warning(tickets) -> None:
    service, clock = tickets
    create(tickets)
    clock.advance(minutes=179)
    service.tick()
    assert not any(e["kind"] == "sla_warning" for e in service.view()[0]["events"])
    clock.advance(minutes=1)
    service.tick()
    service.tick()
    ticket = service.view()[0]
    assert sum(e["kind"] == "sla_warning" for e in ticket["events"]) == 1
    assert not ticket["sla"]["breached"]


def test_breach_auto_escalates(tickets) -> None:
    service, clock = tickets
    create(tickets)
    clock.advance(minutes=240)
    service.tick()
    ticket = service.view()[0]
    event = next(e for e in ticket["events"] if e["kind"] == "sla_breach")
    assert ticket["sla"]["breached"] and ticket["escalated"] and event["destination"] == "supervisor"


def test_runtime_sla_change_recomputes(tickets) -> None:
    service, clock = tickets
    create(tickets)
    create(tickets, "account login fails")
    clock.advance(minutes=60)
    service.tick()
    assert all(not t["sla"]["breached"] for t in service.view())
    get_config_manager().update_runtime_override("tickets.sla_minutes.normal", 30)
    service.tick()
    assert all(t["sla"]["breached"] and t["sla"]["target_minutes"] == 30 for t in service.view())
    assert all(t["sla"]["due_at"] == "2026-10-16T09:30:00+05:30" for t in service.view())
    get_config_manager().update_runtime_override("tickets.sla_minutes.normal", 120)
    service.tick()
    assert all(not t["sla"]["breached"] and t["escalated"] for t in service.view())


def test_handoff_summary_masked(tickets) -> None:
    service, _ = tickets
    values = fields("payment failed with card 4111 1111 1111 1111 and phone +91 9876543210")
    ticket = service.collect("owner", "session", 1, values, {"last_user_request": values["issue"]}, [])
    summary = ticket["handoff_summary"]
    assert all(v not in summary for v in ("4111", "9876543210", "alice@example.com"))
    assert "ORD-4512" in summary and "PRD-007" in summary
    assert "MASKED" in summary


def test_dedup_does_not_cross_customer_order_product_or_owner(tickets) -> None:
    service, _ = tickets
    create(tickets)
    for index, key in enumerate(("customer", "order", "product")):
        values = fields()
        values[key] += "different"
        result = service.collect("owner", "session", 1, values, {}, [])
        assert result["status"] == "QUEUED", index
    service.collect("different-owner", "session", 1, fields(), {}, [])
    assert len([r for r in service.view() if r["status"] == "QUEUED"]) == 5


def test_concurrent_duplicate_creation_is_atomic(tickets) -> None:
    service, _ = tickets
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: create(tickets), range(8)))
    assert len({r["id"] for r in results}) == 1
    ticket = next(r for r in service.view() if r["status"] == "QUEUED")
    assert len(ticket["requests"]) == 8


def test_durable_sla_events_after_restart(tickets) -> None:
    service, clock = tickets
    create(tickets)
    clock.advance(minutes=240)
    other = TicketService(TicketRepository(service.repo.db_path), clock, service.audit, service.metrics)
    try:
        other.tick()
        service.tick()
        assert sum(e["kind"] == "sla_breach" for e in other.view()[0]["events"]) == 1
    finally:
        other.repo.close()


def test_unresolved_chat_collects_separate_drafts_and_reuses_summaries(tickets, tmp_path: Path) -> None:
    _, clock = tickets
    service = ConversationService(SessionManager(SessionRepository(str(tmp_path / "chat.db")), clock), AuditLogger(), MetricsCollector())
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    try:
        result = service.turn("refund order ORD-4512 and track order ORD-5678", "chat", "owner", lambda q: engine.query(q, "customer"))
        assert len(result.tickets) == 2
        assert {t["fields"]["order"] for t in result.tickets} == {"ORD-4512", "ORD-5678"}
        assert all(t["status"] == "DRAFT" and "customer" in t["missing_fields"] for t in result.tickets)
        assert "last_user_request" in result.tickets[0]["handoff_summary"]
        clock.advance(minutes=31)
        again = service.turn("refund order ORD-4512", "chat", "owner", lambda q: engine.query(q, "customer"))
        assert again.session_transition == "RESTORED" and again.summary
    finally:
        service.sessions.repo.close()
        service.support.repo.close()
        service.tickets.repo.close()
        engine.repo.close()


def test_ticket_api_access_and_draft_completion(tickets, tmp_path: Path) -> None:
    _, clock = tickets
    service = ConversationService(SessionManager(SessionRepository(str(tmp_path / "api.db")), clock), AuditLogger(), MetricsCollector())
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    set_task4_engine(engine)
    set_conversation_service(service)
    headers = {"x-api-key": "customer-key-alice"}
    try:
        with TestClient(app) as client:
            reply = client.post("/query", headers=headers, json={"question": "refund order ORD-4512", "session_id": "api"})
            assert reply.status_code == 200
            draft = reply.json()["tickets"][0]
            assert reply.json()["ticket_questions"] == [draft["question"]]
            body = {"session_id": "api", "draft_id": draft["id"], "fields": fields()}
            assert client.post("/tickets", json=body).status_code == 403
            assert client.post("/tickets", headers={"x-api-key": "bad"}, json=body).status_code == 403
            assert client.post("/tickets", headers={"x-api-key": "support-key-bob"}, json=body).status_code == 403
            final = client.post("/tickets", headers=headers, json=body)
            assert final.status_code == 200 and final.json()["status"] == "QUEUED"
            assert final.json()["owner"] == hashlib.sha256(b"customer-key-alice").hexdigest()
            assert client.get("/tickets", headers=headers).json()[0]["id"] == draft["id"]
            assert client.get("/tickets", headers={"x-api-key": "public-key-anon"}).status_code == 403
            closing = {"generation": 1, "reason": "Customer confirmed delivery"}
            assert client.post(f"/tickets/{draft['id']}/close", headers=headers, json=closing).status_code == 403
            assert client.post(f"/tickets/{draft['id']}/close", headers={"x-api-key": "support-key-bob"}, json=closing).json()["status"] == "CLOSED"
    finally:
        service.sessions.repo.close()
        service.support.repo.close()
        service.tickets.repo.close()
        engine.repo.close()


def test_background_ticket_sla_runs_without_next_message(tickets, monkeypatch) -> None:
    import app.chatbot as chatbot
    service, clock = tickets
    conversation = ConversationService(SessionManager(SessionRepository(), clock), service.audit, service.metrics)
    conversation.tickets.repo.close()
    conversation.tickets = service
    set_conversation_service(conversation)
    create(tickets)
    clock.advance(minutes=240)
    updater = SimpleNamespace(tick=lambda: None, audit=service.audit, metrics=service.metrics, clock=clock)
    monkeypatch.setattr(chatbot, "update_service", lambda: updater)
    def stop(seconds):
        raise RuntimeError("one iteration")
    monkeypatch.setattr(clock, "sleep", stop)
    try:
        with pytest.raises(RuntimeError, match="one iteration"):
            asyncio.run(chatbot.maintenance_worker())
        assert service.view()[0]["sla"]["breached"]
    finally:
        conversation.sessions.repo.close()
        conversation.support.repo.close()


def test_calendar_boundaries_and_clock_rewind(tickets) -> None:
    service, clock = tickets
    clock.set("2026-10-16T08:00:00+05:30")
    ticket = create(tickets)
    assert ticket["scheduled_for"] == "2026-10-16T09:00:00+05:30"
    clock.set("2026-10-15T08:00:00+05:30")
    service.tick()
    assert service.view()[0]["sla"]["consumed_minutes"] == 0
    cal = BusinessCalendar()
    assert cal.is_open(clock.now().replace(hour=9))
    assert not cal.is_open(clock.now().replace(hour=18))


def test_similar_wording_with_conflicting_details_is_not_merged(tickets) -> None:
    a = create(tickets, "courier confirmed delivery arrived at front door")
    b = create(tickets, "courier not confirmed delivery arrived at front door")
    c = create(tickets, "delivery parcel tracking error 1234567")
    d = create(tickets, "delivery parcel tracking error 7654321")
    assert len({a["id"], b["id"], c["id"], d["id"]}) == 4


def test_ticket_priority_uses_existing_history_aware_sentiment(tickets) -> None:
    service, _ = tickets
    values = fields("Great service, thanks!")
    result = service.collect("owner", "session", 1, values, {},
                             [{"role": "user", "content": "My delivery is late"}])
    assert result["sentiment"]["label"] == "sarcastic"
    assert result["priority"]["components"]["sentiment"] == 0.8


def test_capacity_released_and_priority_orders_queue(tickets) -> None:
    service, _ = tickets
    low = create(tickets, "delivery parcel delayed", severity="low")
    high = create(tickets, "tracking unavailable", severity="critical")
    get_config_manager().update_runtime_override("tickets.agents", [agent("A", ["delivery"], capacity=1)])
    service.tick()
    indexed = {r["id"]: r for r in service.view()}
    assert indexed[high["id"]]["agent_id"] == "A" and indexed[low["id"]]["agent_id"] is None
    service.close_ticket(high["id"], "Resolved with the customer")
    service.tick()
    assert next(r for r in service.view() if r["id"] == low["id"])["agent_id"] == "A"


def test_invalid_sla_config_rolls_back_all_ticket_changes(tickets) -> None:
    service, clock = tickets
    create(tickets)
    before = service.view()
    clock.advance(minutes=240)
    get_config_manager().update_runtime_override("tickets.sla_minutes.normal", 0)
    with pytest.raises(ValueError, match="positive"):
        service.tick()
    assert service.view() == before


def test_duplicate_merge_preserves_earliest_sla_and_highest_severity(tickets) -> None:
    _, clock = tickets
    initial = create(tickets, severity="normal")
    clock.advance(minutes=20)
    merged = create(tickets, severity="critical", impact="widespread")
    assert merged["id"] == initial["id"] and merged["created_at"] == initial["created_at"]
    assert merged["severity"] == "critical" and merged["impact"] == "widespread"
    assert merged["sla"]["consumed_minutes"] == 20 and merged["sla"]["target_minutes"] == 30
    assert create(tickets, severity="low")["severity"] == "critical"


def test_ticket_timer_survives_sentiment_worker_outage(tickets, monkeypatch) -> None:
    import app.chatbot as chatbot
    service, clock = tickets
    conversation = ConversationService(SessionManager(SessionRepository(), clock), service.audit, service.metrics)
    conversation.tickets.repo.close()
    conversation.tickets = service
    set_conversation_service(conversation)
    create(tickets)
    clock.advance(minutes=240)
    def unavailable():
        raise RuntimeError("sentiment store unavailable")
    monkeypatch.setattr(conversation.support, "tick", unavailable)
    monkeypatch.setattr(chatbot, "update_service", lambda: SimpleNamespace(
        tick=unavailable, audit=service.audit, metrics=service.metrics, clock=clock))
    def stop(seconds):
        raise RuntimeError("one iteration")
    monkeypatch.setattr(clock, "sleep", stop)
    try:
        with pytest.raises(RuntimeError, match="one iteration"):
            asyncio.run(chatbot.maintenance_worker())
        assert service.view()[0]["sla"]["breached"]
    finally:
        conversation.sessions.repo.close()
        conversation.support.repo.close()


def test_explicit_unresolved_request_creates_draft_despite_factual_answer(tickets, tmp_path: Path) -> None:
    _, clock = tickets
    service = ConversationService(SessionManager(SessionRepository(str(tmp_path / "explicit.db")), clock), AuditLogger(), MetricsCollector())
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    engine.load_fixture_directory("data/sample_docs")
    try:
        result = service.turn("What is the refund policy for bootcamp?", "explicit", "owner",
                              lambda q: engine.query(q, "customer"), unresolved=True)
        assert result.verified and result.citations and not result.refusal
        assert result.tickets[0]["status"] == "DRAFT" and result.tickets[0]["question"]
        another = service.turn("This is still unresolved, speak to a human", "human", "owner",
                               lambda q: engine.query(q, "customer"))
        assert another.tickets and another.tickets[0]["fields"]["issue"]
    finally:
        service.sessions.repo.close()
        service.support.repo.close()
        service.tickets.repo.close()
        engine.repo.close()
