"""Ingest-time embedding cache and deterministic test vectors."""

import hashlib
import json
import math
from typing import Any, Protocol


class Embedder(Protocol):
    @property
    def embedding_model(self) -> str: ...

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]: ...


class FakeEmbedder:
    """Scripted vectors only; no claimed semantic inference or live-provider accuracy."""

    def __init__(self, vectors: dict[str, list[float]], model: str = "fake-embedding-v1") -> None:
        self.vectors, self.embedding_model = vectors, model
        self.calls: list[dict[str, Any]] = []
        self.unavailable = False

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        self.calls.append({"texts": list(texts), "task": task})
        if self.unavailable:
            raise RuntimeError("Scripted embedding outage")
        return [list(self.vectors[text]) for text in texts]


def document_text(doc: Any) -> str:
    return f"{doc.section} {doc.product} {doc.content}"


def vector_key(doc: Any) -> str:
    payload = [doc.doc_id, doc.version, doc.product, doc.region, doc.access_level,
               doc.effective_date, doc.expiry_date, document_text(doc)]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()


def validate_vector(value: list[float]) -> list[float]:
    if not value or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in value):
        raise ValueError("Embedding must be a nonempty finite numeric vector")
    if not any(value):
        raise ValueError("Embedding cannot be zero")
    return [float(v) for v in value]


def cosine(first: list[float], second: list[float]) -> float:
    if len(first) != len(second):
        raise ValueError("Embedding dimensions differ")
    first, second = validate_vector(first), validate_vector(second)
    return max(0.0, min(1.0, sum(a*b for a, b in zip(first, second, strict=True)) /
                        math.sqrt(sum(a*a for a in first) * sum(b*b for b in second))))
