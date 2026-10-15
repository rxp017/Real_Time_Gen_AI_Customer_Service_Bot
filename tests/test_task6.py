"""Task 6 scenarios: byte preservation, changing languages, context and session isolation."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.chatbot import app, set_conversation_service, set_task4_engine
from core.audit import AuditLogger
from core.clock import FakeClock, set_global_clock
from core.config import get_config_manager
from core.conversation import ConversationService
from core.language import LanguageProcessor
from core.llm import FakeLLM
from core.metrics import MetricsCollector
from core.retrieval import GenerationResult, PolicyRetrievalEngine
from core.sessions import SessionManager
from core.store import DocumentRepository, SessionRepository


@pytest.fixture
def conversation(tmp_path: Path) -> tuple[ConversationService, FakeClock, PolicyRetrievalEngine]:
    clock = FakeClock("2026-10-13T12:00:00+05:30")
    set_global_clock(clock)
    manager = SessionManager(SessionRepository(str(tmp_path / "sessions.db")), clock)
    service = ConversationService(manager, AuditLogger(), MetricsCollector())
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    engine.load_fixture_directory("data/sample_docs")
    return service, clock, engine


def send(conversation: tuple[ConversationService, FakeClock, PolicyRetrievalEngine], text: str,
         session: str = "test-session", owner: str = "owner") -> Any:
    service, _, engine = conversation
    return service.turn(text, session, owner, lambda q: engine.query(q, "customer"))


@pytest.mark.parametrize("language,text", [
    ("en", "my name is Ána O’Neil, refund order ORD-AbC-4512 on 2026-10-13 product PRD-XyZ-007 please"),
    ("hi", "मेरा नाम Ána O’Neil, मुझे रिफंड चाहिए ऑर्डर ORD-AbC-4512 2026-10-13 PRD-XyZ-007"),
    ("te", "నా పేరు Ána O’Neil, నాకు రీఫండ్ కావాలి ఆర్డర్ ORD-AbC-4512 2026-10-13 PRD-XyZ-007"),
    ("es", "me llamo Ána O’Neil, quiero reembolso pedido ORD-AbC-4512 2026-10-13 PRD-XyZ-007"),
])
def test_entities_preserved_across_languages(language: str, text: str) -> None:
    processor = LanguageProcessor()
    analysis = processor.analyze(text)
    assert analysis.detection.language == language
    expected = {"name": "Ána O’Neil", "order_id": "ORD-AbC-4512", "date": "2026-10-13", "product_code": "PRD-XyZ-007"}
    assert {e.kind: e.value for e in analysis.protected.entities} == expected
    restored = analysis.protected.restore(analysis.normalized)
    for value in expected.values():
        assert value.encode("utf-8") in restored.encode("utf-8")
        assert value not in analysis.normalized
    assert analysis.protected.restore(analysis.protected.text).encode("utf-8") == text.encode("utf-8")
    localized, _ = processor.localize("Learners are eligible for a 100% full refund within 14 days of course enrollment. "
                                     + text + " [DOC-REFUND-V2, v2, Refund Policy]", language)
    for value in expected.values():
        assert value.encode("utf-8") in localized.encode("utf-8")
    assert "[DOC-REFUND-V2, v2, Refund Policy]" in localized


def test_mixed_language_message(conversation) -> None:
    result = send(conversation, "mujhe refund chahiye please help mera order ORD-4512")
    assert result.language == "hi"
    assert result.mixed_language
    assert {"hi", "en"}.issubset(result.detected_languages)
    assert result.requests[0]["intent"] == "refund"
    assert not result.clarification_needed
    assert result.context["order_id"] == "ORD-4512"


def test_language_switch_mid_conversation(conversation) -> None:
    for language, text in [("en", "refund policy order 4512"), ("hi", "मुझे रिफंड चाहिए"),
                           ("te", "నాకు రీఫండ్ కావాలి"), ("es", "Quiero un reembolso")]:
        result = send(conversation, text)
        assert result.language == language
        assert result.context["order_id"] == "4512"
        assert not result.clarification_needed


def test_context_retained_10_messages(conversation) -> None:
    service, _, _ = conversation
    send(conversation, "refund policy order 4512")
    for _ in range(10):
        send(conversation, "any update on it?")
    state = service.sessions.inspect("test-session", "owner")
    assert len(state["messages"]) == 10
    assert state["message_count"] == 22
    assert state["entities"]["order_id"] == "4512"
    get_config_manager().update_runtime_override("conversation.context_messages", 20)
    for _ in range(5):
        send(conversation, "any update on it?")
    assert len(service.sessions.inspect("test-session", "owner")["messages"]) == 20


def test_concurrent_sessions_isolated(conversation) -> None:
    service, _, _ = conversation
    workers = 8
    barrier = Barrier(workers)

    def work(index: int) -> Any:
        order = str(6000 + index)
        llm = FakeLLM(default_response=f"Scripted reply for order {order}")

        def responder(question: str) -> GenerationResult:
            barrier.wait(timeout=20)
            assert order in question
            assert not any(str(6000 + j) in question for j in range(workers) if j != index)
            return GenerationResult(llm.generate(question).content, verified=False)

        return service.turn(f"refund policy order {order}", f"session-{index}", f"owner-{index}", responder)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(work, range(workers)))
    for i, result in enumerate(results):
        assert result.context["order_id"] == str(6000 + i)
        state = service.sessions.inspect(f"session-{i}", f"owner-{i}")
        assert len(state["messages"]) == 2
        assert state["entities"]["order_id"] == str(6000 + i)
        state["entities"]["order_id"] = "tampered copy"
        assert service.sessions.inspect(f"session-{i}", f"owner-{i}")["entities"]["order_id"] == str(6000 + i)


@pytest.mark.parametrize("text", ["xyz qzx blorp", "maybe status", "मौसम बहुत अच्छा है", "zzzzz refund nonsense qqq"])
def test_low_confidence_asks_clarification(conversation, text: str) -> None:
    service, _, _ = conversation

    def must_not_call(question: str) -> GenerationResult:
        pytest.fail("Uncertain message must not reach the answering provider")

    result = service.turn(text, "uncertain", "owner", must_not_call)
    assert result.clarification_needed
    assert not result.citations


@pytest.mark.parametrize("language,text,intent", [
    ("en", "I need refnd please", "refund"),
    ("hi", "mujhey refnd chahie", "refund"),
    ("hi", "mera order kab ayega", "delivery_status"),
    ("te", "naku dabbu tirigi kavali", "refund"),
    ("te", "naa order epudu vasthundi", "delivery_status"),
    ("es", "Quiero rembolso por favor", "refund"),
])
def test_misspelling_and_transliteration(conversation, language: str, text: str, intent: str) -> None:
    result = send(conversation, text)
    assert result.language == language
    assert {r["intent"] for r in result.requests} == {intent}
    assert not result.clarification_needed


@pytest.mark.parametrize("text", ["refund policy and track my order 4512", "मुझे रिफंड चाहिए और डिलीवरी बताओ",
                                    "నాకు రీఫండ్ కావాలి మరియు డెలివరీ వివరాలు", "Quiero reembolso y ver la entrega"])
def test_multiple_requests_in_one_message(conversation, text: str) -> None:
    result = send(conversation, text)
    assert {r["intent"] for r in result.requests} == {"refund", "delivery_status"}
    assert len(result.requests) == 2
    assert not result.clarification_needed
    assert len(result.answer.splitlines()) == 2


def test_correction_overrides_earlier_value(conversation) -> None:
    service, _, _ = conversation
    send(conversation, "refund policy order 4512")
    result = send(conversation, "sorry, order 4521 not 4512")
    assert result.context["order_id"] == "4521"
    state = service.sessions.inspect("test-session", "owner")
    assert any(e["value"] == "4512" for e in state["superseded"])
    assert "4521" in result.answer
    followup = send(conversation, "any update on it?")
    assert "4521" in followup.context["order_id"]
    assert "4512" not in followup.requests[0]["question"]
    assert followup.requests[0]["inherited"]


def test_session_expires_after_30min(conversation) -> None:
    service, clock, _ = conversation
    send(conversation, "refund policy order 4512")
    clock.advance(minutes=29, seconds=59)
    assert service.sessions.inspect("test-session", "owner")["status"] == "ACTIVE"
    clock.advance(seconds=1)
    assert service.sessions.expire_idle() == 1
    state = service.sessions.inspect("test-session", "owner")
    assert state["status"] == "EXPIRED"
    assert state["summary"]["entities"]["order_id"] == "4512"


def test_return_within_24h_restores_summary(conversation) -> None:
    _, clock, _ = conversation
    send(conversation, "refund policy order 4512")
    send(conversation, "sorry, order 4521 not 4512")
    clock.advance(hours=23)
    result = send(conversation, "any update on it?")
    assert result.session_transition == "RESTORED"
    assert result.summary["entities"]["order_id"] == "4521"
    assert any(e["value"] == "4512" for e in result.summary["superseded"])
    assert result.context["order_id"] == "4521"
    assert result.generation == 1
    assert result.requests[0]["intent"] == "refund"


def test_return_after_24h_new_session(conversation) -> None:
    _, clock, _ = conversation
    send(conversation, "refund policy order 4512")
    clock.advance(hours=24, seconds=1)
    result = send(conversation, "refund policy")
    assert result.session_transition == "NEW_AFTER_RETENTION"
    assert result.generation == 2
    assert result.summary is None
    assert result.context == {}


def test_config_changes_thresholds_without_code(conversation) -> None:
    service, _, _ = conversation
    text = "mujhey refnd chahie"
    assert not send(conversation, text).clarification_needed
    get_config_manager().update_runtime_override("thresholds.language_confidence", 0.99)
    assert send(conversation, text).clarification_needed
    get_config_manager().update_runtime_override("thresholds.language_confidence", 0.6)
    get_config_manager().update_runtime_override("thresholds.intent_confidence", 0.99)
    assert send(conversation, text).clarification_needed
    assert service.language.analyze(text).requests[0].confidence == 0.95


def test_unseen_conversation_set(conversation) -> None:
    seen = {m["text"] for code in ("en", "hi", "te", "es")
            for c in json.loads(Path(f"tests/fixtures/{code}.json").read_text(encoding="utf-8")) for m in c["messages"]}
    cases = json.loads(Path("tests/fixtures/unseen.json").read_text(encoding="utf-8"))
    for case in cases:
        for message in case["messages"]:
            assert message["text"] not in seen
            result = send(conversation, message["text"], case["id"])
            assert result.language == case["language"], case["id"]
            assert set(message["intents"]) == {r["intent"] for r in result.requests}, case["id"]
            assert not result.clarification_needed, case["id"]


@pytest.mark.parametrize("language", ["en", "hi", "te", "es"])
def test_fixture_conversations_per_language(conversation, language: str) -> None:
    cases = json.loads(Path(f"tests/fixtures/{language}.json").read_text(encoding="utf-8"))
    assert len(cases) >= 30
    assert len({c["messages"][0]["text"] for c in cases}) == len(cases)
    for case in cases:
        for message in case["messages"]:
            result = send(conversation, message["text"], case["id"])
            assert result.language == language, (case["id"], message["text"], result.language)
            assert set(message["intents"]) == {r["intent"] for r in result.requests}, (case["id"], message["text"])
            assert not result.clarification_needed, (case["id"], message["text"], result.requests)
        assert result.context["order_id"] == case["latest_order"]
        state = conversation[0].sessions.inspect(case["id"], "owner")
        assert any(e["value"] == case["superseded_order"] for e in state["superseded"])


def test_language_added_using_config_and_resources_only(conversation, tmp_path: Path) -> None:
    import shutil

    resource_dir = tmp_path / "languages"
    shutil.copytree("resources/languages", resource_dir)
    resource = json.loads((resource_dir / "en.json").read_text(encoding="utf-8"))
    resource.update(markers=["bonjour", "regles"], replacements=[{"pattern": "regles", "value": "refund policy"}],
                    entities=[], messages={"clarification": "Précisez la demande.", "correction": "Correction enregistrée."}, intents={})
    (resource_dir / "fr.json").write_text(json.dumps(resource), encoding="utf-8")
    manager = get_config_manager()
    manager.update_runtime_override("languages", ["en", "hi", "te", "es", "fr"])
    manager.update_runtime_override("conversation.resource_directory", str(resource_dir))
    result = send(conversation, "bonjour regles")
    assert result.language == "fr"
    assert result.requests[0]["intent"] == "refund"
    assert not result.clarification_needed


def test_sessions_survive_restart_and_owner_mismatch_rejected(conversation) -> None:
    service, clock, _ = conversation
    send(conversation, "refund policy order 4512")
    repo_path = service.sessions.repo.db_path
    service.sessions.repo.close()
    service.sessions = SessionManager(SessionRepository(repo_path), clock)
    assert send(conversation, "any update on it?").context["order_id"] == "4512"
    with pytest.raises(PermissionError):
        send(conversation, "refund policy", owner="different-owner")


def test_entity_placeholder_loss_or_user_spoof_is_rejected() -> None:
    protected = LanguageProcessor().analyze("refund order 4512").protected
    with pytest.raises(ValueError):
        protected.restore("lost placeholder")
    with pytest.raises(ValueError):
        LanguageProcessor().analyze("refund __ENTITY_abcd_0__")


def test_session_timings_are_hot_configurable(conversation) -> None:
    service, clock, _ = conversation
    manager = get_config_manager()
    manager.update_runtime_override("timings.session_inactivity_timeout_minutes", 1)
    manager.update_runtime_override("timings.session_restore_hours", 2)
    send(conversation, "refund policy order 4512")
    clock.advance(minutes=1)
    assert service.sessions.inspect("test-session", "owner")["status"] == "EXPIRED"
    clock.advance(hours=2)
    assert send(conversation, "refund policy").session_transition == "NEW_AFTER_RETENTION"


def test_api_multilingual_context_and_owner_binding(conversation) -> None:
    service, _, engine = conversation
    set_conversation_service(service)
    set_task4_engine(engine)
    client = TestClient(app)
    headers = {"x-api-key": "customer-key-alice"}
    first = client.post("/query", json={"question": "refund policy order 4512"}, headers=headers)
    assert first.status_code == 200
    session = first.json()["session_id"]
    second = client.post("/query", json={"question": "Quiero un reembolso", "session_id": session}, headers=headers)
    assert second.status_code == 200
    assert second.json()["language"] == "es"
    assert second.json()["context"]["order_id"] == "4512"
    forbidden = client.post("/query", json={"question": "refund policy", "session_id": session},
                            headers={"x-api-key": "support-key-bob"})
    assert forbidden.status_code == 403


def test_multiple_requests_keep_separate_entity_bindings(conversation) -> None:
    service, _, _ = conversation
    calls = []

    def responder(question: str) -> GenerationResult:
        calls.append(question)
        return GenerationResult(FakeLLM(default_response="Offline refusal").generate(question).content,
                                refusal=True, verified=False)

    result = service.turn("track order 4512 and cancel order 4521", "two-orders", "owner", responder)
    assert len(calls) == 2
    assert "4512" in calls[0] and "4521" not in calls[0]
    assert "4521" in calls[1] and "4512" not in calls[1]
    assert result.requests[0]["context"]["order_id"] == "4512"
    assert result.requests[1]["context"]["order_id"] == "4521"
    followup = service.turn("any update on it?", "two-orders", "owner", responder)
    assert followup.clarification_needed
    assert len(calls) == 2


@pytest.mark.parametrize("text,expected", [
    ("My name is Zoë Smith, refund order 00004512 13 October 2026 PRD-07", "Zoë Smith"),
    ("मेरा नाम राज शेखर, रिफंड ऑर्डर 00004512 13 अक्टूबर 2026 PRD-07", "राज शेखर"),
    ("నా పేరు రాజ శేఖర్, రీఫండ్ ఆర్డర్ 00004512 13 అక్టోబర్ 2026 PRD-07", "రాజ శేఖర్"),
    ("Mi nombre es José García, reembolso pedido 00004512 13 de octubre de 2026 PRD-07", "José García"),
])
def test_native_names_named_dates_and_leading_zero_orders(text: str, expected: str) -> None:
    analysis = LanguageProcessor().analyze(text)
    entities = {e.kind: e.value for e in analysis.protected.entities}
    assert entities["name"] == expected
    assert entities["order_id"] == "00004512"
    assert entities["product_code"] == "PRD-07"
    assert entities["date"] in text
    restored = analysis.protected.restore(analysis.normalized)
    assert all(v.encode("utf-8") in restored.encode("utf-8") for v in entities.values())


def test_provider_failure_does_not_half_commit_session(conversation) -> None:
    service, _, _ = conversation
    send(conversation, "refund policy order 4512")

    def unavailable(question: str) -> GenerationResult:
        raise ConnectionError("provider down")

    with pytest.raises(ConnectionError):
        service.turn("refund policy order 4521", "test-session", "owner", unavailable)
    state = service.sessions.inspect("test-session", "owner")
    assert state["entities"]["order_id"] == "4512"
    assert state["message_count"] == 2


def test_same_session_concurrent_updates_do_not_lose_messages(conversation) -> None:
    service, _, engine = conversation
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: service.turn(f"refund policy order {7000+i}", "same-session", "owner",
                                            lambda q: engine.query(q, "customer")), range(8)))
    state = service.sessions.inspect("same-session", "owner")
    assert state["message_count"] == 16
    assert len(state["messages"]) == 10
    values = {e["value"] for e in state["superseded"]} | {state["entities"]["order_id"]}
    assert values == {str(7000+i) for i in range(8)}


def test_exactly_24h_restores_and_clock_reset_is_not_wall_time(conversation) -> None:
    _, clock, _ = conversation
    send(conversation, "refund policy order 4512")
    clock.advance(hours=24)
    result = send(conversation, "any update on it?")
    assert result.session_transition == "RESTORED"
    assert result.context["order_id"] == "4512"


def test_entities_from_one_request_do_not_pollute_another_request(conversation) -> None:
    service, _, _ = conversation
    calls = []

    def responder(question: str) -> GenerationResult:
        calls.append(question)
        return GenerationResult("Test-only refusal", refusal=True)

    service.turn("refund order 4512 and product price PRD-XyZ", "bindings", "owner", responder)
    assert "4512" in calls[0] and "PRD-XyZ" not in calls[0]
    assert "PRD-XyZ" in calls[1] and "4512" not in calls[1]


def test_concurrent_turns_with_persistent_audit_and_metrics(conversation, tmp_path: Path) -> None:
    from core.store import AuditLogRepository, MetricsRepository

    service, _, _ = conversation
    audit_repo = AuditLogRepository(str(tmp_path / "sessions.db"))
    metrics_repo = MetricsRepository(str(tmp_path / "sessions.db"))
    service.audit = AuditLogger(audit_repo)
    service.metrics = MetricsCollector(metrics_repo)
    barrier = Barrier(8)

    def work(i: int) -> Any:
        def responder(question: str) -> GenerationResult:
            barrier.wait(timeout=20)
            return GenerationResult(FakeLLM(default_response="Offline reply").generate(question).content, verified=False)
        return service.turn(f"refund policy order {8000+i}", f"persist-{i}", "owner", responder)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, range(8)))
    assert len(results) == 8
    assert len(audit_repo.get_recent(100)) == 8
    assert service.metrics.get_summary()["values"]["language_confidence"]["count"] == 8
    assert metrics_repo.conn.execute("SELECT COUNT(*) FROM metric_values WHERE name='language_confidence'").fetchone()[0] == 8
    assert all(result.context["order_id"] == str(8000+i) for i, result in enumerate(results))
    audit_repo.close()
    metrics_repo.close()


@pytest.mark.parametrize("text", ["I need a refund please", "mujhe refund chahiye", "naaku refund kavali", "Quiero un reembolso"])
def test_multilingual_request_filler_does_not_hide_grounded_policy(conversation, text: str) -> None:
    result = send(conversation, text)
    assert result.verified
    assert not result.refusal
    assert result.citations[0]["doc_id"] == "DOC-REFUND-V2"


def test_retrieval_filler_removal_preserves_entities_and_negation() -> None:
    processor = LanguageProcessor()
    analysis = processor.analyze("my name is Quiero, refund order ORD-PLEASE-001 not on 2026-10-14 PRD-NEED-002 please")
    restored = analysis.protected.restore(processor.retrieval_text(analysis.normalized))
    assert "Quiero" in restored
    assert "ORD-PLEASE-001" in restored
    assert "PRD-NEED-002" in restored
    assert "2026-10-14" in restored
    assert "not" in restored


def test_curated_translation_accepts_citation_punctuation_spacing() -> None:
    processor = LanguageProcessor()
    source = "Learners are eligible for a 100% full refund within 14 days of course enrollment . [DOC-REFUND-V2, v2, Refund Policy]"
    translated, changed = processor.localize(source, "es")
    assert changed
    assert "Los estudiantes" in translated
    assert "[DOC-REFUND-V2, v2, Refund Policy]" in translated
