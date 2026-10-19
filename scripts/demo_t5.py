"""Offline Task 5 history, risk, calendar routing, tone, and timer demonstration."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit import AuditLogger  # noqa: E402
from core.clock import FakeClock, set_global_clock  # noqa: E402
from core.config import get_config_manager  # noqa: E402
from core.conversation import ConversationService  # noqa: E402
from core.llm import FakeLLM  # noqa: E402
from core.metrics import MetricsCollector  # noqa: E402
from core.retrieval import PolicyRetrievalEngine  # noqa: E402
from core.sessions import SessionManager  # noqa: E402
from core.store import DocumentRepository, SessionRepository  # noqa: E402


def main() -> None:
    clock = FakeClock("2026-10-16T20:00:00+05:30")
    set_global_clock(clock)
    config = get_config_manager()
    config.update_runtime_override("holidays", ["2026-10-19"])
    config.update_runtime_override("support.repeated_negative_count", 2)
    with TemporaryDirectory(dir=".verification", prefix="task5-demo-") as folder:
        sessions = SessionRepository(str(Path(folder) / "demo.db"))
        service = ConversationService(SessionManager(sessions, clock), AuditLogger(), MetricsCollector())
        engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
        engine.load_fixture_directory("data/sample_docs")
        report = {"mode": "Offline FakeClock/FakeLLM fixture demonstration", "turns": []}
        for sid, message in [
            ("risk", "Please note someone accessed my account"),
            ("normal", "refund policy is terrible"),
            ("normal", "Any update on it again?"),
            ("sarcasm", "delivery is late"),
            ("sarcasm", "Wonderful service!"),
            ("timer", "The product is broken"),
        ]:
            result = service.turn(message, sid, "demo-owner", lambda q: engine.query(q, "customer"))
            report["turns"].append({"message": message, "sentiment": result.sentiment,
                                    "high_risk": result.high_risk, "answer": result.answer,
                                    "tone_prefix": result.tone_prefix, "escalations": result.escalations})
        clock.advance(minutes=15, seconds=1)
        report["background_timer_records"] = service.support.tick()
        report["metrics"] = service.metrics.get_summary()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        service.tickets.repo.close()
        service.support.repo.close()
        sessions.close()
        engine.repo.close()


if __name__ == "__main__":
    main()
