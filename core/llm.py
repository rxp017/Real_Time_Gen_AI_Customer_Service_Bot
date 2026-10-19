"""LLM Client interface and adapters.

Defines the LLMClient contract, a real provider adapter, and a deterministic FakeLLM
for hermetic test execution without network access.
"""

import base64
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import parsedate_to_datetime
from threading import RLock
from typing import Any

import httpx

from core.clock import Clock, get_clock
from core.config import get_config
from core.provider_retry import post_with_retry


@dataclass
class LLMResponse:
    """Unified response container for LLM generation."""

    content: str
    model: str = "mock-model"
    usage: dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    attempts: list[dict[str, Any]] = field(default_factory=list)


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @property
    def supports_vision(self) -> bool:
        return False

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response text for the provided prompt."""


class FakeLLM(LLMClient):
    """Deterministic, scripted LLM implementation for tests without network access."""

    def __init__(
        self,
        default_response: str = "Mock answer based on context.",
        responses: list[str] | None = None,
        response_map: dict[str, str] | None = None,
        supports_vision: bool = False,
    ) -> None:
        self.default_response = default_response
        self._responses_queue: list[str] = list(responses) if responses else []
        self._response_map: dict[str, str] = dict(response_map) if response_map else {}
        self.calls: list[dict[str, Any]] = []
        self._vision = supports_vision

    @property
    def supports_vision(self) -> bool:
        return self._vision

    def set_response_for(self, prompt_substring: str, response: str) -> None:
        """Map a prompt substring to a deterministic response."""
        self._response_map[prompt_substring] = response

    def enqueue_response(self, response: str) -> None:
        """Add a response to the sequential FIFO queue."""
        self._responses_queue.append(response)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        self.calls.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "kwargs": kwargs,
        })

        # 1. Check mapped patterns
        for key, mapped_resp in self._response_map.items():
            if key in prompt or (system_prompt and key in system_prompt):
                return LLMResponse(content=mapped_resp, model="fake-llm-mapped")

        # 2. Check queued FIFO responses
        if self._responses_queue:
            return LLMResponse(content=self._responses_queue.pop(0), model="fake-llm-queue")

        # 3. Grounded fallback if data boundary exists and using default response
        import re
        from html import unescape
        boundary_match = re.search(r"<data_boundary[^>]*>\s*(.*?)\s*</data_boundary>", prompt, re.DOTALL)
        if boundary_match and self.default_response == "Mock answer based on context.":
            clean_context = unescape(boundary_match.group(1).strip())
            citation = re.search(r"You MUST cite the source as (\[[^\]]+\])", prompt)
            cite = citation.group(1) if citation else ""
            return LLMResponse(content=f"{clean_context} {cite}".strip(), model="fake-llm-grounded")

        # 4. Fallback default
        return LLMResponse(content=self.default_response, model="fake-llm-default")


class ProviderUnavailableError(RuntimeError):
    """All configured models failed, cooled down, or exceeded the request budget."""

    def __init__(self, attempts: list[dict[str, Any]], reason: str | None = None) -> None:
        self.reason = reason or ("quota" if any(a.get("status") == 429 for a in attempts) else "infrastructure")
        super().__init__("Live AI quota is blocked; retry later." if self.reason.startswith("quota")
                         else "No configured Gemini model is available; retry later.")
        self.attempts = attempts


class ProviderBlockedError(RuntimeError):
    """Provider refused the content; switching models must not bypass this decision."""


class ProviderAuthenticationError(RuntimeError):
    """Credentials or permissions were rejected; model switching cannot fix the key."""


class RealProviderAdapter(LLMClient):
    """Real provider adapter using standard REST endpoints or official SDKs."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 fallback_models: list[str] | None = None, clock: Clock | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GOOGLE_API_KEY", "")
        self.model = model if model is not None else os.getenv("GOOGLE_MODEL", "")
        self.fallback_models = fallback_models
        self.clock = clock
        self._cooldowns: dict[str, float] = {}
        self._last_failure_status: int | None = None
        self._lock = RLock()

    def configured_models(self) -> list[str]:
        cfg = get_config()
        if self.fallback_models is not None:
            fallbacks = self.fallback_models
        elif "GOOGLE_FALLBACK_MODELS" in os.environ:
            fallbacks = [m.strip() for m in os.environ["GOOGLE_FALLBACK_MODELS"].split(",") if m.strip()]
        else:
            fallbacks = list(cfg.get("provider.fallback_models"))
        models = list(dict.fromkeys([self.model, *fallbacks]))
        if any(not re.fullmatch(r"[A-Za-z0-9._-]+", m) for m in models):
            raise ValueError("Invalid provider model name")
        if cfg.get("provider.restrict_to_catalog") and any(m not in cfg.get("provider.free_tier_eligible_models") for m in models):
            raise ValueError("Configured model is outside the verified free-tier-eligible catalog")
        return models

    @property
    def embedding_model(self) -> str:
        return str(get_config().get("retrieval.embedding_model"))

    @property
    def supports_embeddings(self) -> bool:
        return bool(self.api_key)

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        from core.embeddings import validate_vector

        if not self.api_key or task not in {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}:
            raise ValueError("Embedding credentials and a valid task are required")
        if not texts:
            return []
        model = self.embedding_model
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise ValueError("Invalid embedding model")
        clock = self.clock or get_clock()
        attempts: list[dict[str, Any]] = []
        try:
            response = post_with_retry(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents",
                {"requests": [{"model": "models/" + model, "content": {"parts": [{"text": text}]},
                                    "taskType": task} for text in texts]},
                self.api_key, model, clock,
                clock.monotonic() + float(get_config().get("provider.request_budget_seconds")), attempts,
                int(get_config().get("provider.max_retries")),
            )
        except httpx.RequestError:
            raise ProviderUnavailableError([*attempts, {"model": model, "status": "transport"}]) from None
        if response.status_code != 200:
            raise ProviderUnavailableError(attempts)
        values = response.json().get("embeddings", [])
        if len(values) != len(texts):
            raise ValueError("Embedding response count mismatch")
        return [validate_vector(item["values"]) for item in values]

    @property
    def supports_vision(self) -> bool:
        return bool(self.api_key and self.model in get_config().get("provider.vision_capable_models", []))

    def _cool_down(self, model: str, clock: Clock, retry_after: str | None = None) -> None:
        cfg = get_config()
        delay = float(cfg.get("provider.cooldown_seconds"))
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                try:
                    stamp = parsedate_to_datetime(retry_after)
                    if stamp.tzinfo is None:
                        stamp = stamp.replace(tzinfo=timezone.utc)
                    delay = max(delay, (stamp - clock.now()).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    delay = float(cfg.get("provider.cooldown_seconds"))
        delay = min(delay, float(cfg.get("provider.max_cooldown_seconds")))
        with self._lock:
            self._cooldowns[model] = clock.monotonic() + delay

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.api_key or not self.model:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_MODEL must be configured.")
        cfg = get_config()
        models = self.configured_models()
        images = kwargs.get("images", [])
        if images:
            if not self.supports_vision:
                raise ValueError("Configured provider does not support image input")
            models = [m for m in models if m in cfg.get("provider.vision_capable_models")]
        clock = self.clock or get_clock()
        deadline = clock.monotonic() + float(cfg.get("provider.request_budget_seconds"))
        attempts: list[dict[str, Any]] = []
        body: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                                "generationConfig": {"temperature": temperature,
                                                     "maxOutputTokens": int(cfg.get("provider.max_output_tokens"))}}
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        for img in images:
            if img.get("mime_type") not in {"image/png", "image/jpeg"} or not isinstance(img.get("data"), bytes):
                raise ValueError("Invalid inline image input")
            body["contents"][0]["parts"].append({"inlineData": {"mimeType": img["mime_type"],
                                                                  "data": base64.b64encode(img["data"]).decode("ascii")}})
        for model in models:
            remaining = deadline - clock.monotonic()
            if remaining <= 0 or len(attempts) >= int(cfg.get("provider.max_model_attempts")):
                break
            with self._lock:
                if self._cooldowns.get(model, 0.0) > clock.monotonic():
                    continue
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                # Preserve immediate fallback to another configured model, then retry the final model.
                retries = min(int(cfg.get("provider.max_retries")),
                              max(0, int(cfg.get("provider.max_model_attempts")) - len(attempts) - 1)) if model == models[-1] else 0
                response = post_with_retry(url, body, self.api_key, model, clock, deadline, attempts, retries)
            except httpx.RequestError as exc:
                attempts.append({"model": model, "status": type(exc).__name__})
                self._cool_down(model, clock)
                continue
            if response.status_code in (401, 403):
                raise ProviderAuthenticationError("Gemini credentials or permissions were rejected.") from None
            if response.status_code in cfg.get("provider.fallback_http_statuses"):
                self._last_failure_status = response.status_code
                self._cool_down(model, clock, response.headers.get("retry-after"))
                continue
            if response.status_code != 200:
                raise RuntimeError(f"Gemini rejected the request with HTTP {response.status_code}.") from None
            try:
                data = response.json()
                if data.get("promptFeedback", {}).get("blockReason"):
                    raise ProviderBlockedError("Gemini blocked the request; no model fallback attempted.")
                candidates = data.get("candidates", [])
                candidate = candidates[0] if candidates else {}
                if candidate.get("finishReason") in {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY"}:
                    raise ProviderBlockedError("Gemini blocked the response; no model fallback attempted.")
                text = "".join(p["text"] for p in candidate.get("content", {}).get("parts", [])
                               if isinstance(p.get("text"), str) and not p.get("thought", False))
                if not text.strip():
                    raise ValueError("No generated text")
                metadata = data.get("usageMetadata", {})
                usage = {target: int(metadata[source]) for source, target in
                         (("promptTokenCount", "prompt_tokens"), ("candidatesTokenCount", "completion_tokens"),
                          ("totalTokenCount", "total_tokens")) if source in metadata}
            except (ValueError, TypeError, KeyError, AttributeError):
                attempts[-1]["status"] = "invalid_response"
                self._cool_down(model, clock)
                continue
            return LLMResponse(content=text, model=model, usage=usage, attempts=attempts)
        reason = "quota_cooldown" if not attempts and self._last_failure_status == 429 else None
        raise ProviderUnavailableError(attempts, reason) from None
