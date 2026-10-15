"""Measure explicit multilingual fixtures and disjoint wording with the shared offline bot."""

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.audit import AuditLogger
from core.clock import FakeClock, set_global_clock
from core.config import get_config
from core.conversation import ConversationService
from core.llm import FakeLLM
from core.metrics import MetricsCollector
from core.retrieval import PolicyRetrievalEngine
from core.sessions import SessionManager
from core.store import DocumentRepository, SessionRepository


def evaluate() -> dict[str, Any]:
    clock = FakeClock("2026-10-13T12:00:00+05:30")
    set_global_clock(clock)
    session_repo = SessionRepository()
    documents = DocumentRepository()
    engine = PolicyRetrievalEngine(documents, FakeLLM())
    engine.load_fixture_directory(ROOT / "data/sample_docs")
    service = ConversationService(SessionManager(session_repo, clock), AuditLogger(), MetricsCollector())
    result: dict[str, Any] = {"mode": "offline resource rules; FakeClock/FakeLLM, real SQLite",
                              "languages": {}, "failures": []}
    seen = set()
    for code in get_config().languages:
        cases = json.loads((ROOT / f"tests/fixtures/{code}.json").read_text(encoding="utf-8"))
        stats = {"conversations": len(cases), "messages": 0, "language_correct": 0, "intent_correct": 0, "clarifications": 0}
        for case in cases:
            for message in case["messages"]:
                seen.add(message["text"])
                response = service.turn(message["text"], case["id"], "fixture-owner", lambda q: engine.query(q, "customer"))
                language_ok = response.language == code
                intent_ok = {r["intent"] for r in response.requests} == set(message["intents"])
                stats["messages"] += 1
                stats["language_correct"] += int(language_ok)
                stats["intent_correct"] += int(intent_ok)
                stats["clarifications"] += int(response.clarification_needed)
                if not language_ok or not intent_ok or response.clarification_needed:
                    result["failures"].append({"conversation": case["id"], "message": message["text"]})
        result["languages"][code] = stats
    unseen = json.loads((ROOT / "tests/fixtures/unseen.json").read_text(encoding="utf-8"))
    stats = {"conversations": len(unseen), "messages": 0, "language_correct": 0, "intent_correct": 0,
             "clarifications": 0, "overlap_with_fixture_wording": 0}
    for case in unseen:
        for message in case["messages"]:
            response = service.turn(message["text"], case["id"], "fixture-owner", lambda q: engine.query(q, "customer"))
            language_ok = response.language == case["language"]
            intent_ok = {r["intent"] for r in response.requests} == set(message["intents"])
            stats["messages"] += 1
            stats["language_correct"] += int(language_ok)
            stats["intent_correct"] += int(intent_ok)
            stats["clarifications"] += int(response.clarification_needed)
            stats["overlap_with_fixture_wording"] += int(message["text"] in seen)
            if not language_ok or not intent_ok or response.clarification_needed:
                result["failures"].append({"conversation": case["id"], "message": message["text"]})
    result["unseen"] = stats
    result["limitation"] = "Authored domain examples and unseen wording do not establish general language accuracy."
    session_repo.close()
    documents.close()
    return result


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["failures"] or result["unseen"]["overlap_with_fixture_wording"]:
        raise SystemExit(1)
