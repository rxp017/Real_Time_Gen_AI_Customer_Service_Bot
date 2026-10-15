"""Send one synthetic probe via the fallback adapter; persist sanitized results only."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from core.clock import get_clock
from core.llm import ProviderUnavailableError, RealProviderAdapter


def probe() -> dict[str, object]:
    load_dotenv(ROOT / ".env", override=True)
    clock = get_clock()
    started = clock.monotonic()
    adapter = RealProviderAdapter()
    try:
        result = adapter.generate("Reply with only the word READY.", "This is a synthetic connectivity probe. Return READY.")
        report = {"status": "ok", "model": result.model, "attempts": result.attempts,
                  "usage": result.usage, "probe_matches": result.content.strip() == "READY"}
    except ProviderUnavailableError as exc:
        report = {"status": "unavailable", "attempts": exc.attempts}
    except (RuntimeError, ValueError) as exc:
        report = {"status": "failed", "error_type": type(exc).__name__}
    report["elapsed_seconds"] = round(clock.monotonic() - started, 3)
    report["note"] = "Synthetic probe only; does not certify project billing tier or chatbot quality."
    (ROOT / "docs/verification/provider-generation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
