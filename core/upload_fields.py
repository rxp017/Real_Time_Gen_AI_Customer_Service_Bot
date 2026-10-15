"""Explicit field evidence and deterministic customer/document comparisons."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from core.config import get_config
from core.ocr import TextLine


def extract_fields(lines: list[TextLine], patterns: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    fields = {}
    for name, pattern in (patterns or get_config().get("uploads.field_patterns")).items():
        candidates: dict[Any, dict[str, Any]] = {}
        for line in lines:
            for match in re.finditer(pattern, line.text):
                value = next(value for value in match.groupdict().values() if value is not None).strip()
                key = canonical(value, name)
                candidate = {"value": value, "confidence": line.confidence,
                             "source_region": {"page": line.page, "bbox": list(line.bbox),
                                               "units": line.units, "origin": line.origin}}
                if key not in candidates or line.confidence > candidates[key]["confidence"]:
                    candidates[key] = candidate
        if len(candidates) == 1:
            fields[name] = next(iter(candidates.values()))
        else:
            fields[name] = {"value": None, "confidence": 0.0, "source_region": None}
            if candidates:
                fields[name]["candidates"] = list(candidates.values())
    return fields


def canonical(value: str, field: str) -> Any:
    if field == "date":
        for fmt in get_config().get("uploads.date_formats"):
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue
        return value
    if field == "amount":
        aliases = get_config().get("uploads.currency_aliases")
        prefix = re.sub(r"[\d,.\s]", "", value)
        currency = next((v for k, v in aliases.items() if k.rstrip(".").casefold() == prefix.casefold()), None)
        try:
            numeric = re.search(r"\d[\d,]*(?:\.\d{1,2})?", value)
            return Decimal(numeric[0].replace(",", "")), currency
        except InvalidOperation:
            return value
    return value


def compare_fields(fields: dict[str, dict[str, Any]], customer_message: str) -> list[dict[str, Any]]:
    customer = extract_fields([TextLine(customer_message, 1.0, 0, (0, 0, 0, 0))],
                              get_config().get("uploads.customer_field_patterns"))
    conflicts = []
    for name in ("order_id", "amount", "date"):
        found = fields[name]
        if found.get("candidates"):
            conflicts.append({"field": name, "document": [c["value"] for c in found["candidates"]],
                              "customer": customer[name]["value"], "reason": "multiple_document_values"})
            continue
        expected = customer[name]
        if expected.get("candidates"):
            conflicts.append({"field": name, "document": found["value"],
                              "customer": [c["value"] for c in expected["candidates"]], "reason": "multiple_customer_values"})
            continue
        if found["value"] is None or expected["value"] is None:
            continue
        actual, stated = canonical(found["value"], name), canonical(expected["value"], name)
        same = actual == stated
        if name == "amount" and isinstance(actual, tuple) and isinstance(stated, tuple):
            same = actual[0] == stated[0] and (not actual[1] or not stated[1] or actual[1] == stated[1])
        if not same:
            conflicts.append({"field": name, "document": found["value"], "customer": expected["value"], "reason": "mismatch"})
    return conflicts
