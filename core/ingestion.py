"""Strict policy-file validation, canonical hashes, and evidence-preserving quarantine."""

import hashlib
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from core.config import get_config
from core.security import detect_prompt_injection


class InvalidFile(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return "\n".join(line.rstrip() for line in unicodedata.normalize("NFC", value)
                         .replace("\r\n", "\n").replace("\r", "\n").strip().split("\n"))
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def read_policy(path: Path) -> tuple[dict[str, Any], str]:
    if path.stat().st_size > int(get_config().get("updates.max_file_bytes")):
        raise InvalidFile("oversize")
    raw = path.read_bytes()
    if not raw.strip():
        raise InvalidFile("empty")
    if path.suffix.lower() not in get_config().get("updates.supported_types"):
        raise InvalidFile("unsupported type")
    try:
        data = normalize(json.loads(raw.decode("utf-8-sig")))
    except (UnicodeError, ValueError):
        raise InvalidFile("corrupt") from None
    fields = {"doc_id", "version", "product", "region", "access_level", "effective_date",
              "expiry_date", "doc_family", "section", "content"}
    if not isinstance(data, dict) or fields - data.keys():
        raise InvalidFile("missing metadata")
    if any(not isinstance(data[k], str) or not data[k] for k in fields - {"version", "expiry_date"}):
        raise InvalidFile("missing metadata")
    if not isinstance(data["version"], int) or isinstance(data["version"], bool) or data["version"] < 1:
        raise InvalidFile("corrupt")
    if data["access_level"] not in get_config().roles:
        raise InvalidFile("missing metadata")
    try:
        start = datetime.fromisoformat(data["effective_date"])
        expiry = data["expiry_date"]
        end = datetime.fromisoformat(expiry) if expiry is not None else None
        zone = ZoneInfo(get_config().timezone)
        if start.tzinfo is None:
            start = start.replace(tzinfo=zone)
        if end is not None:
            if end.tzinfo is None:
                end = end.replace(tzinfo=zone)
            if end <= start:
                raise ValueError("Invalid date range")
    except (ValueError, TypeError):
        raise InvalidFile("corrupt") from None
    if any(detect_prompt_injection(v)[0] for v in data.values() if isinstance(v, str)):
        raise InvalidFile("injection-flagged")
    # Source labels cannot smuggle forged citations or structural delimiters.
    if any(any(c in data[k] for c in "[]<>\n") for k in ("doc_id", "section", "doc_family")):
        raise InvalidFile("injection-flagged")
    data = {k: data[k] for k in fields}
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return data, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def quarantine(path: Path, root: Path, reason: str) -> Path:
    folder = root / uuid4().hex
    folder.mkdir(parents=True)
    (folder / "payload").write_bytes(path.read_bytes())
    (folder / "reason.json").write_text(json.dumps({"reason": reason}), encoding="utf-8")
    return folder
