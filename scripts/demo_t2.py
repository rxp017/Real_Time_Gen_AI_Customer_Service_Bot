"""Actual offline gate/OCR/PDF extraction results on synthetic file fixtures."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit import AuditLogger
from core.config import get_config_manager
from core.upload_gate import UploadGate, UploadRejected
from core.upload_processing import UploadProcessor


def main() -> None:
    get_config_manager().update_runtime_override("uploads.vision_model", "")
    root = Path("tests/fixtures/task2")
    gate, processor = UploadGate(AuditLogger()), UploadProcessor()
    results = []
    for name in ("clean.png", "clean.jpg", "clean.pdf", "scanned.pdf", "blurred.png", "mismatched.png",
                 "missing.png", "injected.png", "injected.pdf", "injected-scan.pdf", "hidden-injected.pdf",
                 "active.pdf", "malformed.png", "product.png", "product-no-text.png"):
        path = root / name
        mime = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg"}[path.suffix]
        try:
            data = path.read_bytes()
            gated = gate.validate(data, name, mime)
            result = processor.process(data, gated, "Order ID: ORD-1001; Amount: INR 1299.00; Date: 2026-10-15",
                                       "product" if name.startswith("product") else "invoice", "en")
        except UploadRejected as exc:
            result = {"status": "rejected", "reason": exc.reason}
        results.append({"fixture": name, **result})
    print(json.dumps({"mode": "Real local Tesseract/PDFium, no network or vision inference", "results": results}, indent=2))


if __name__ == "__main__":
    main()
