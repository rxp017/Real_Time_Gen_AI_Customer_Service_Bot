"""Optional manual real-provider smoke check; synthetic product image, no PII."""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit import AuditLogger
from core.clock import get_clock
from core.config import get_config
from core.llm import ProviderUnavailableError
from core.upload_gate import UploadGate
from core.upload_processing import UploadProcessor


def main() -> None:
    load_dotenv(override=False)
    clock = get_clock()
    start = clock.monotonic()
    path = Path("tests/fixtures/task2/product.png")
    data = path.read_bytes()
    gate = UploadGate(AuditLogger()).validate(data, path.name, "image/png")
    try:
        result = UploadProcessor().process(data, gate, "Describe the visible product only.", "product", "en")
    except ProviderUnavailableError as exc:
        result = {"status": "cannot analyse", "error_type": type(exc).__name__, "attempts": exc.attempts}
    except Exception as exc:  # noqa: BLE001 - sanitized diagnostic, never print request headers or credentials
        result = {"status": "cannot analyse", "error_type": type(exc).__name__}
    print(json.dumps({"scope": "One manual real-provider smoke check on a synthetic product label",
                      "configured_model": get_config().get("uploads.vision_model"),
                      "elapsed_ms": (clock.monotonic() - start) * 1000, "result": result}, indent=2))


if __name__ == "__main__":
    main()
