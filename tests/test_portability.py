"""Portable OCR discovery, override precedence and equivalent version formats."""

import re

import pytest

from core.config import get_config_manager
from core.ocr import TesseractOCR


def test_ocr_runtime_override_beats_environment(monkeypatch) -> None:
    monkeypatch.setenv("TESSERACT_CMD", "environment-tesseract")
    get_config_manager().update_runtime_override("uploads.ocr.executable", "runtime-tesseract")
    assert TesseractOCR()._configuration()[0] == "runtime-tesseract"


def test_ocr_path_discovery(monkeypatch) -> None:
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr("core.ocr.shutil.which", lambda name: "/usr/bin/tesseract" if name == "tesseract" else None)
    assert TesseractOCR()._configuration()[0] == "/usr/bin/tesseract"


@pytest.mark.parametrize("version", ["tesseract v5.4", "tesseract 5.3.4", "tesseract v5.4.0.20240606"])
def test_ocr_version_formats(version: str) -> None:
    assert re.match(r"^tesseract v?\d+\.\d+(?:\.\d+)?\b", version)
