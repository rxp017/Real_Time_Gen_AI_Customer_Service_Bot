"""Deadline-bounded HTTP retries; waiting is always delegated to Clock."""

import math
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from core.clock import Clock
from core.config import get_config


def retry_delay(response: httpx.Response, clock: Clock, attempt: int) -> float:
    cfg = get_config()
    delay = min(float(cfg.get("provider.retry_max_seconds")),
                float(cfg.get("provider.retry_base_seconds")) * 2 ** attempt)
    header = response.headers.get("retry-after")
    if header:
        try:
            requested = float(header)
        except ValueError:
            try:
                stamp = parsedate_to_datetime(header)
                requested = (stamp.replace(tzinfo=stamp.tzinfo or timezone.utc) - clock.now()).total_seconds()
            except (ValueError, TypeError, OverflowError):
                requested = 0.0
        if math.isfinite(requested):
            delay = max(delay, requested)
    try:
        for detail in response.json().get("error", {}).get("details", []):
            if str(detail.get("@type", "")).endswith("google.rpc.RetryInfo"):
                requested = float(str(detail.get("retryDelay", "0s")).removesuffix("s"))
                if math.isfinite(requested):
                    delay = max(delay, requested)
    except (ValueError, TypeError, AttributeError):
        # Malformed provider hints never shorten the configured backoff.
        delay = max(delay, 0.0)
    return max(0.0, delay)


def post_with_retry(url: str, body: dict[str, Any], key: str, model: str, clock: Clock,
                    deadline: float, attempts: list[dict[str, Any]], retries: int) -> httpx.Response:
    cfg = get_config()
    for index in range(retries + 1):
        remaining = deadline - clock.monotonic()
        if remaining <= 0:
            raise TimeoutError("Provider request deadline exhausted")
        response = httpx.post(url, json=body, headers={"x-goog-api-key": key},
                              timeout=min(float(cfg.get("provider.timeout_seconds")), remaining))
        attempts.append({"model": model, "status": response.status_code})
        if response.status_code == 429:
            try:
                limits = []
                for detail in response.json().get("error", {}).get("details", []):
                    if str(detail.get("@type", "")).endswith("google.rpc.QuotaFailure"):
                        for item in detail.get("violations", []):
                            limits.append({key: str(item[key])[:160] for key in ("quotaId", "quotaValue") if key in item})
                attempts[-1]["quota_limits"] = limits
            except (ValueError, TypeError, AttributeError):
                attempts[-1]["quota_limits"] = []
        if response.status_code != 429 or index == retries:
            return response
        delay = retry_delay(response, clock, index)
        attempts[-1]["retry_after_seconds"] = delay
        if delay >= deadline - clock.monotonic():
            attempts[-1]["retry_skipped"] = "deadline"
            return response
        clock.sleep(delay)
    raise RuntimeError("Unreachable retry state")
