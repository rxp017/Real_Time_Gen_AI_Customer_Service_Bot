"""Protect original entity spans before any text transformation."""

import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Entity:
    kind: str
    value: str
    token: str
    start: int
    end: int
    usage: str = "current"


@dataclass(frozen=True)
class ProtectedText:
    original: str
    text: str
    entities: tuple[Entity, ...]

    def restore(self, transformed: str, require_all: bool = True) -> str:
        for entity in self.entities:
            if require_all and transformed.count(entity.token) != 1:
                raise ValueError("Entity placeholder missing or duplicated by transformation")
            transformed = transformed.replace(entity.token, entity.value)
        return transformed


class EntityProtector:
    def protect(self, text: str, patterns: list[dict[str, Any]], token_pattern: str) -> ProtectedText:
        if re.search(token_pattern, text):
            raise ValueError("Reserved entity token supplied in user text")
        spans: list[tuple[int, int, str, str]] = []
        for rule in patterns:
            for match in re.finditer(rule["pattern"], text, re.IGNORECASE):
                groups = rule.get("groups", {"value": "current"})
                for group, usage in groups.items():
                    if match.group(group) is None:
                        continue
                    start, end = match.span(group)
                    if start == end or any(start < e and end > s for s, e, _, _ in spans):
                        continue
                    spans.append((start, end, rule["kind"], usage))
        nonce = uuid4().hex
        spans.sort()
        entities = tuple(Entity(kind, text[start:end], f"__ENTITY_{nonce}_{i}__", start, end, usage)
                         for i, (start, end, kind, usage) in enumerate(spans))
        protected = text
        for entity in reversed(entities):
            protected = protected[:entity.start] + entity.token + protected[entity.end:]
        return ProtectedText(text, protected, entities)
