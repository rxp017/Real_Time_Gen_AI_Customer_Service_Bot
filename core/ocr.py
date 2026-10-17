"""Real local Tesseract checks, TSV text regions, and image quality evidence."""

import csv
import io
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from PIL import Image, ImageFilter, ImageOps, ImageStat

from core.config import get_config, get_config_manager


@dataclass(frozen=True)
class TextLine:
    text: str
    confidence: float
    page: int
    bbox: tuple[float, float, float, float]
    units: str = "pixels"
    origin: str = "top_left"


def blur_score(image: Image.Image) -> float:
    if image.width < 5 or image.height < 5:
        return 0.0
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges.crop((2, 2, edges.width - 2, edges.height - 2))).var[0])


class TesseractOCR:
    def __init__(self) -> None:
        self._checked: tuple[str, str, tuple[str, ...]] | None = None
        self._lock = RLock()

    def _configuration(self) -> tuple[str, str, tuple[str, ...]]:
        cfg = get_config()
        configured = str(cfg.get("uploads.ocr.executable"))
        explicit = get_config_manager().has_runtime_override("uploads.ocr.executable")
        executable = configured if explicit else os.getenv("TESSERACT_CMD") or configured
        found = shutil.which(executable)
        if found:
            executable = found
        elif executable == "tesseract" and os.name == "nt":
            fallback = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
            if fallback.is_file():
                executable = str(fallback)
        directory = cfg.get("uploads.ocr.tessdata_directory") or ""
        if not directory:
            local = Path(".runtime/tessdata")
            if local.is_dir():
                directory = str(local)
        return executable, directory, tuple(cfg.get("uploads.ocr.languages").values())

    def check(self) -> dict[str, Any]:
        executable, directory, required = self._configuration()
        timeout = float(get_config().get("uploads.ocr.process_timeout_seconds"))
        version = subprocess.run([executable, "--version"], capture_output=True, timeout=timeout, check=True)
        options = ["--tessdata-dir", directory] if directory else []
        langs = subprocess.run([executable, *options, "--list-langs"],
                               capture_output=True, timeout=timeout, check=True)
        available = [line.strip() for line in langs.stdout.decode("utf-8").splitlines()[1:] if line.strip()]
        missing = sorted(set(required) - set(available))
        if missing:
            raise RuntimeError("Missing Tesseract language packs: " + ", ".join(missing))
        with self._lock:
            self._checked = executable, directory, required
        return {"executable": executable, "version": version.stdout.decode("utf-8").splitlines()[0],
                "available_languages": available, "required_languages": list(required), "missing_languages": missing}

    def recognize(self, image: Image.Image, page: int, language: str) -> tuple[list[TextLine], float]:
        cfg = get_config()
        if language not in cfg.get("uploads.ocr.languages"):
            raise ValueError("Unsupported OCR language")
        with self._lock:
            if self._checked != self._configuration():
                self.check()
        executable, directory, _ = self._configuration()
        data = io.BytesIO()
        ImageOps.autocontrast(image.convert("L")).save(data, format="PNG")
        response = subprocess.run(
            [executable, "stdin", "stdout", *(["--tessdata-dir", directory] if directory else []),
             "-l", cfg.get("uploads.ocr.languages")[language], "--oem", "1",
             "--psm", str(cfg.get("uploads.ocr.page_segmentation")),
             "-c", "tessedit_create_tsv=1", "-c", "tessedit_create_txt=0"],
            input=data.getvalue(), capture_output=True, check=True,
            timeout=float(cfg.get("uploads.ocr.process_timeout_seconds")),
        )
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        confidences = []
        for row in csv.DictReader(io.StringIO(response.stdout.decode("utf-8-sig")), delimiter="\t"):
            if row["level"] != "5" or not row["text"].strip():
                continue
            confidence = max(0.0, min(1.0, float(row["conf"]) / 100))
            confidences.append(confidence)
            key = tuple(row[k] for k in ("block_num", "par_num", "line_num"))
            grouped.setdefault(key, []).append({"text": row["text"], "confidence": confidence,
                                               "x": int(row["left"]), "y": int(row["top"]),
                                               "w": int(row["width"]), "h": int(row["height"])})
        lines = [TextLine(" ".join(w["text"] for w in words), min(w["confidence"] for w in words), page,
                          (min(w["x"] for w in words), min(w["y"] for w in words),
                           max(w["x"] + w["w"] for w in words), max(w["y"] + w["h"] for w in words)))
                 for words in grouped.values()]
        return lines, sum(confidences) / len(confidences) if confidences else 0.0
