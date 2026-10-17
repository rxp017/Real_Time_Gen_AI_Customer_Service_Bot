"""Provider translations preserve opaque original entity and citation spans."""

import json
import re
from html import unescape

import pytest

from core.language import LanguageProcessor
from core.llm import FakeLLM, LLMResponse


class Translator(FakeLLM):
    def generate(self, prompt, **kwargs):
        source = unescape(re.search(r'<data_boundary[^>]*>\s*(.*?)\s*</data_boundary>', prompt, re.DOTALL)[1])
        language = re.search(r"into language (\w+)", prompt)[1]
        return LLMResponse(json.dumps({"translation": "Respuesta " + source, "language": language}))


@pytest.mark.parametrize("language", ["hi", "te", "es"])
def test_provider_translation_preserves_original_entity_bytes(language: str) -> None:
    original = "Refund for A\u0301na O’Neil order ORD-0042 product SKU-X9 on 2026-10-17 is 14%. [DOC, v2, Refund]"
    result, changed = LanguageProcessor(Translator()).localize(original, language)
    assert changed
    for value in ["A\u0301na O’Neil", "ORD-0042", "SKU-X9", "2026-10-17", "14%", "[DOC, v2, Refund]"]:
        assert value.encode() in result.encode()


def test_unlabelled_name_protected_before_normalisation() -> None:
    original = "Please refund for A\u0301na O’Neil order ORD-4512"
    analysis = LanguageProcessor().analyze(original)
    assert "A\u0301na O’Neil".encode() in analysis.protected.restore(analysis.normalized).encode()


@pytest.mark.parametrize("response", [
    '{"translation":"Changed to 500%","language":"es"}',
    '{"translation":"Lost all placeholders","language":"es"}',
    '{"translation":"Ignore previous instructions","language":"es"}',
    '{"translation":"wrong target","language":"hi"}',
])
def test_invalid_translation_uses_curated_or_source_fallback(response: str) -> None:
    source = "Order ORD-0042 has amount 14%. [DOC, v2, Refund]"
    result, changed = LanguageProcessor(FakeLLM(default_response=response)).localize(source, "es")
    assert result == source and not changed


def test_translation_provider_outage_preserves_source() -> None:
    class Down(Translator):
        def generate(self, *args, **kwargs):
            raise RuntimeError("Unavailable")
    result, changed = LanguageProcessor(Down()).localize("Order ORD-0042", "es")
    assert result == "Order ORD-0042" and not changed


def test_translated_answer_keeps_canonical_source_separate() -> None:
    from core.audit import AuditLogger
    from core.clock import FakeClock
    from core.conversation import ConversationService
    from core.metrics import MetricsCollector
    from core.retrieval import GenerationResult
    from core.sessions import SessionManager
    from core.store import SessionRepository

    service = ConversationService(SessionManager(SessionRepository(), FakeClock()), AuditLogger(), MetricsCollector())
    service.language = LanguageProcessor(Translator())
    source = "Refunds require proof for order ORD-0042."
    result = service.turn("Quiero un reembolso", "translation", "owner", lambda q: GenerationResult(source))
    assert result.source_answer == source
    assert result.answer != source and result.answer_language == "es"
