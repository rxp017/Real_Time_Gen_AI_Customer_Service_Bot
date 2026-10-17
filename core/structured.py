"""Parse complete provider JSON, optionally enclosed in a JSON code fence."""

import json
import re
from typing import Any


def provider_json(text: str) -> Any:
    value = text.strip()
    wrapped = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", value, re.DOTALL)
    return json.loads(wrapped[1] if wrapped else value)
