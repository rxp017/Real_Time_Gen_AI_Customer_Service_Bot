"""Evaluation-only pacing, reproducible vector cache and binomial intervals."""

import gzip
import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any

from core.clock import SystemClock
from core.config import get_config
from core.embeddings import validate_vector
from core.llm import LLMClient, ProviderUnavailableError, RealProviderAdapter


def wilson(successes: int, total: int) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": total, "rate": None, "wilson95": None}
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    radius = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {"successes": successes, "total": total, "rate": p,
            "wilson95": [max(0, centre - radius), min(1, centre + radius)]}


class PacedProvider(LLMClient):
    """No production request spacing; only the evaluator waits between live operations."""

    def __init__(self) -> None:
        self.clock = SystemClock()
        self.delegate = RealProviderAdapter(fallback_models=[], clock=self.clock)
        self.model = self.delegate.model
        self.next_call = 0.0

    def wait(self) -> None:
        delay = self.next_call - self.clock.monotonic()
        if delay > 0:
            self.clock.sleep(delay)
        self.next_call = self.clock.monotonic() + float(get_config().get("evaluation.request_spacing_seconds"))

    def generate(self, *args: Any, **kwargs: Any):
        if any(self.delegate._cooldowns.get(model, 0) <= self.clock.monotonic()
               for model in self.delegate.configured_models()):
            self.wait()
        try:
            return self.delegate.generate(*args, **kwargs)
        except ProviderUnavailableError as exc:
            status = "QUOTA_BLOCKED" if any(a.get("status") == 429 for a in exc.attempts) else "PROVIDER_UNAVAILABLE_OR_COOLDOWN"
            print(f"STATUS {status}: live call unavailable; fallback is not provider success", flush=True)
            raise


class EvaluationVectors:
    """Read actual previously measured vectors by content/model hash, never invented vectors."""

    def __init__(self, provider: PacedProvider, path: Path) -> None:
        self.provider = provider
        self.embedding_model = provider.delegate.embedding_model
        self.path = path
        artifact = Path("docs/verification/revision-dev-vectors.json.gz")
        self.values = (json.loads(path.read_text()) if path.exists() else
                       json.loads(gzip.decompress(artifact.read_bytes())) if artifact.exists() else {})
        self.errors: list[dict[str, Any]] = []

    def key(self, text: str, task: str) -> str:
        return hashlib.sha256((self.embedding_model + "\0" + task + "\0" + text).encode()).hexdigest()

    def warm(self, texts: list[str], task: str) -> None:
        missing = list(dict.fromkeys(t for t in texts if self.key(t, task) not in self.values))
        for index in range(0, len(missing), 16):
            batch = missing[index:index + 16]
            self.provider.wait()
            try:
                vectors = self.provider.delegate.embed(batch, task)
                for text, vector in zip(batch, vectors, strict=True):
                    self.values[self.key(text, task)] = validate_vector(vector)
                self.path.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.path.with_suffix(".tmp")
                temporary.write_text(json.dumps(self.values))
                temporary.replace(self.path)
            except (RuntimeError, ValueError, OSError) as exc:
                self.errors.append({"batch_size": len(batch), "attempts": getattr(exc, "attempts", []), "error": type(exc).__name__})
                print("STATUS EMBEDDING_UNAVAILABLE: lexical fallback will be reported", flush=True)

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        try:
            return [self.values[self.key(text, task)] for text in texts]
        except KeyError:
            raise ProviderUnavailableError([{"model": self.embedding_model, "status": "uncached_after_warm_failure"}]) from None
