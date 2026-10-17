"""Browser boundaries and customer controls use actual API routes without a provider."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.chatbot import app, set_task4_engine
from core.clock import FakeClock, set_global_clock
from core.config import get_config_manager
from core.llm import FakeLLM
from core.retrieval import PolicyRetrievalEngine
from core.store import DocumentRepository


def client() -> TestClient:
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    engine.load_fixture_directory("data/sample_docs")
    set_task4_engine(engine)
    return TestClient(app)


def test_customer_page_has_chat_upload_tickets_and_no_admin_controls() -> None:
    response = client().get("/")
    assert response.status_code == 200
    assert all(name in response.text for name in ('id="chat-form"', 'id="upload-form"', 'id="ticket-form"'))
    script = Path("app/web/app.js").read_text()
    assert "textContent" in script
    assert all(unsafe not in script for unsafe in ("innerHTML", "outerHTML", "insertAdjacentHTML", "localStorage", "sessionStorage", "/knowledge", "/close"))
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_unknown_cross_origin_is_rejected_before_processing() -> None:
    api = client()
    response = api.post("/query", json={"question": "refund policy"}, headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers
    allowed = api.options("/query", headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "POST"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:8000"
    assert "*" not in allowed.headers["access-control-allow-origin"]


def test_rate_limiting_uses_clock_and_survives_key_changes() -> None:
    clock = FakeClock()
    set_global_clock(clock)
    get_config_manager().update_runtime_override("web.requests_per_window", 1)
    api = client()
    assert api.post("/query", json={"question": "refund policy for bootcamp"}).status_code == 200
    second = api.post("/query", json={"question": "refund policy"}, headers={"x-api-key": "different"})
    assert second.status_code == 429 and second.headers["retry-after"]
    clock.advance(seconds=61)
    assert api.post("/query", json={"question": "refund policy for bootcamp"}).status_code == 200


def test_json_body_limit_before_application_parsing() -> None:
    get_config_manager().update_runtime_override("web.max_json_bytes", 20)
    response = client().post("/query", content=b'{"question":"' + b"a"*100 + b'"}', headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_client_configuration_contains_no_credentials() -> None:
    data = client().get("/client-config").json()
    assert set(data) == {"languages", "max_upload_bytes", "upload_types"}
    assert data["max_upload_bytes"] == 8388608
