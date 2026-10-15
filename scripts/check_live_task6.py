"""Synthetic fixture queries through the real provider and Task 6 wrapper; no customer data."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from core.audit import AuditLogger
from core.clock import FakeClock, SystemClock, set_global_clock
from core.conversation import ConversationService
from core.llm import LLMResponse, RealProviderAdapter
from core.metrics import MetricsCollector
from core.retrieval import PolicyRetrievalEngine
from core.sessions import SessionManager
from core.store import DocumentRepository, SessionRepository


def probe() -> dict[str, object]:
    load_dotenv(ROOT / ".env", override=True)
    clock = FakeClock("2026-10-14T12:00:00+05:30")
    set_global_clock(clock)
    repo = DocumentRepository()
    sessions = SessionRepository()
    class ObservedAdapter(RealProviderAdapter):
        last_response: LLMResponse | None = None

        def generate(self, *args, **kwargs) -> LLMResponse:
            result = super().generate(*args, **kwargs)
            self.last_response = result
            return result

    adapter = ObservedAdapter(clock=SystemClock())
    engine = PolicyRetrievalEngine(repo, adapter)
    engine.load_fixture_directory(ROOT / "data/sample_docs")
    service = ConversationService(SessionManager(sessions, clock), AuditLogger(), MetricsCollector())
    cases = []
    for language, question in [("en", "What is the refund policy for bootcamp?"), ("hi", "रिफंड नीति क्या है"),
                               ("te", "రీఫండ్ విధానం ఏమిటి"), ("es", "Cuál es la política de reembolso")]:
        try:
            result = service.turn(question, "synthetic-live-session", "synthetic-owner", lambda q: engine.query(q, "customer"))
            cases.append({"expected_language": language, "language": result.language, "answer_language": result.answer_language,
                          "verified": result.verified, "refusal": result.refusal, "clarification": result.clarification_needed,
                          "citations": result.citations, "session_transition": result.session_transition,
                          "answer": result.answer,
                          "provider_model": adapter.last_response.model if adapter.last_response else None,
                          "provider_output": adapter.last_response.content.replace(adapter.api_key, "[MASKED_SECRET]") if adapter.last_response else None})
        except (RuntimeError, ValueError) as exc:
            cases.append({"expected_language": language, "error_type": type(exc).__name__})
    report = {"mode": "Real Gemini generation; synthetic fixture policy; fixed FakeClock; local SQLite",
              "cases": cases, "passed": all(c.get("language") == c["expected_language"] and c.get("verified")
                                           and not c.get("refusal") and not c.get("clarification") for c in cases)}
    repo.close()
    sessions.close()
    path = ROOT / "docs/verification/task6-live-provider.json"
    history = ROOT / "docs/verification/task6-live-provider-runs.jsonl"
    with history.open("a", encoding="utf-8") as output:
        if path.exists() and not history.stat().st_size:
            output.write(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False) + "\n")
        output.write(json.dumps(report, ensure_ascii=False) + "\n")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
