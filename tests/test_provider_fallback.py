"""Offline provider failures with fake time and HTTP responses; no real credentials."""

from typing import Any

import httpx
import pytest

from core.clock import FakeClock
from core.config import get_config_manager
from core.llm import (
    ProviderAuthenticationError,
    ProviderBlockedError,
    ProviderUnavailableError,
    RealProviderAdapter,
)

PRIMARY = "gemini-3.5-flash-lite"
BACKUP = "gemini-3.1-flash-lite"


def response(status: int, data: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status, json=data or {}, headers=headers,
                          request=httpx.Request("POST", "https://generativelanguage.googleapis.com"))


def answer(text: str = "Grounded response") -> dict[str, Any]:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}],
            "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3, "totalTokenCount": 8}}


@pytest.mark.parametrize("status", [404, 408, 429, 500, 502, 503, 504])
def test_fallback_on_recoverable_http_status(monkeypatch, status: int) -> None:
    calls = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        assert kwargs["headers"]["x-goog-api-key"] == "test-secret"
        assert "test-secret" not in url
        assert kwargs["json"]["generationConfig"]["maxOutputTokens"] == 1024
        return response(status) if len(calls) == 1 else response(200, answer())

    monkeypatch.setattr(httpx, "post", post)
    llm = RealProviderAdapter("test-secret", PRIMARY, [BACKUP], FakeClock())
    result = llm.generate("Question", "Ground facts")
    assert result.model == BACKUP
    assert result.content == "Grounded response"
    assert result.usage["total_tokens"] == 8
    assert [a["status"] for a in result.attempts] == [status, 200]
    assert len(calls) == 2


def test_fallback_on_transport_timeout(monkeypatch) -> None:
    count = 0

    def post(url: str, **kwargs: Any) -> httpx.Response:
        nonlocal count
        count += 1
        if count == 1:
            raise httpx.ReadTimeout("test transport timeout")
        return response(200, answer())

    monkeypatch.setattr(httpx, "post", post)
    assert RealProviderAdapter("test-secret", PRIMARY, [BACKUP]).generate("Question").model == BACKUP


@pytest.mark.parametrize("status", [401, 403, 400])
def test_authentication_and_bad_requests_do_not_switch_models(monkeypatch, status: int) -> None:
    calls = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        return response(status, {"error": {"message": "test-secret must never escape"}})

    monkeypatch.setattr(httpx, "post", post)
    expected = ProviderAuthenticationError if status in (401, 403) else RuntimeError
    with pytest.raises(expected) as caught:
        RealProviderAdapter("test-secret", PRIMARY, [BACKUP]).generate("Question")
    assert len(calls) == 1
    assert "test-secret" not in str(caught.value)


@pytest.mark.parametrize("data", [{"promptFeedback": {"blockReason": "SAFETY"}},
                                 {"candidates": [{"finishReason": "SAFETY"}]}])
def test_safety_blocks_never_trigger_fallback(monkeypatch, data: dict[str, Any]) -> None:
    calls = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        return response(200, data)

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(ProviderBlockedError):
        RealProviderAdapter("test-secret", PRIMARY, [BACKUP]).generate("Question")
    assert len(calls) == 1


def test_all_models_unavailable_is_real_failure_with_cooldown(monkeypatch) -> None:
    calls = []
    clock = FakeClock()

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        return response(429, headers={"retry-after": "120"})

    monkeypatch.setattr(httpx, "post", post)
    llm = RealProviderAdapter("test-secret", PRIMARY, [BACKUP], clock)
    with pytest.raises(ProviderUnavailableError) as caught:
        llm.generate("Question")
    assert len(caught.value.attempts) == 2
    assert len(calls) == 2
    clock.advance(seconds=119)
    with pytest.raises(ProviderUnavailableError):
        llm.generate("Question")
    assert len(calls) == 2
    clock.advance(seconds=1)
    with pytest.raises(ProviderUnavailableError):
        llm.generate("Question")
    assert len(calls) == 4


def test_provider_request_budget_and_max_attempts_are_configurable(monkeypatch) -> None:
    clock = FakeClock()
    manager = get_config_manager()
    manager.update_runtime_override("provider.request_budget_seconds", 2)
    manager.update_runtime_override("provider.max_model_attempts", 1)
    calls = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        assert kwargs["timeout"] == 2
        clock.advance(seconds=3)
        return response(503)

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(ProviderUnavailableError):
        RealProviderAdapter("test-secret", PRIMARY, [BACKUP], clock).generate("Question")
    assert len(calls) == 1


def test_fallback_deduplication_and_no_paid_model_selection(monkeypatch) -> None:
    calls = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append(url)
        return response(503)

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(ProviderUnavailableError):
        RealProviderAdapter("test-secret", PRIMARY, [PRIMARY, BACKUP, BACKUP]).generate("Question")
    assert len(calls) == 2
    with pytest.raises(ValueError, match="catalog"):
        RealProviderAdapter("test-secret", "gemini-4-argon", [BACKUP]).generate("Question")
    assert len(calls) == 2


def test_invalid_response_falls_back_but_thought_text_is_not_returned(monkeypatch) -> None:
    count = 0

    def post(url: str, **kwargs: Any) -> httpx.Response:
        nonlocal count
        count += 1
        if count == 1:
            return response(200, {"candidates": []})
        return response(200, {"candidates": [{"content": {"parts": [
            {"text": "internal thought", "thought": True}, {"text": "Visible"}, {"text": " answer"}]}}]})

    monkeypatch.setattr(httpx, "post", post)
    result = RealProviderAdapter("test-secret", PRIMARY, [BACKUP]).generate("Question")
    assert result.content == "Visible answer"
    assert result.model == BACKUP


def test_env_fallback_models_used_without_key_rotation(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_MODEL", PRIMARY)
    monkeypatch.setenv("GOOGLE_FALLBACK_MODELS", BACKUP)
    llm = RealProviderAdapter(api_key="test-secret")
    assert llm.configured_models() == [PRIMARY, BACKUP]


def test_retry_after_http_date_uses_clock(monkeypatch) -> None:
    clock = FakeClock("2026-10-14T12:00:00+00:00")
    llm = RealProviderAdapter("test-secret", PRIMARY, [], clock)
    llm._cool_down(PRIMARY, clock, "Wed, 14 Oct 2026 12:03:00 GMT")
    assert llm._cooldowns[PRIMARY] == clock.monotonic() + 180
