"""Real installed OCR executable and required language-pack verification."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.ocr import TesseractOCR

if __name__ == "__main__":
    print(json.dumps(TesseractOCR().check(), indent=2))
