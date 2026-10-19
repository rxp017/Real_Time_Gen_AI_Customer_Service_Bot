"""Record a real synthetic translation result without inferring missing success."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.language import LanguageProcessor  # noqa: E402
from core.llm import LLMClient  # noqa: E402
from scripts.evaluation_support import PacedProvider  # noqa: E402


class Recorder(LLMClient):
    def __init__(self) -> None:
        self.delegate = PacedProvider()
        self.calls = []

    def generate(self, *args, **kwargs):
        try:
            response = self.delegate.generate(*args, **kwargs)
            self.calls.append({"model": response.model, "attempts": response.attempts, "http_success": True})
            return response
        except (RuntimeError, OSError) as exc:
            self.calls.append({"error": type(exc).__name__, "attempts": getattr(exc, "attempts", []), "http_success": False})
            raise


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    provider = Recorder()
    language = LanguageProcessor(provider=provider)
    source = "Order ORD-7418 for Ravi Kumar has amount EUR 42.50 on 2026-10-19 for SKU-M72."
    protected = ["ORD-7418", "Ravi Kumar", "42.50", "2026-10-19", "SKU-M72"]
    outcomes = []
    for code in ("hi", "te", "es"):
        start = len(provider.calls)
        result, changed = language.localize(source, code)
        calls = provider.calls[start:]
        preserved = all(value.encode("utf-8") in result.encode("utf-8") for value in protected)
        success = changed and preserved and any(c["http_success"] for c in calls)
        outcomes.append({"language": code, "source": source, "answer": result, "entity_bytes_preserved": preserved,
                         "successful_live_translation": success, "calls": calls})
        print(f"STATUS TRANSLATION_{'SUCCESS' if success else 'FALLBACK'} language={code}", flush=True)
    report = {"scope": "Real provider, synthetic entity-preservation probe; meaning is not independently certified", "outcomes": outcomes}
    Path("docs/verification/revision-translation-live.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
