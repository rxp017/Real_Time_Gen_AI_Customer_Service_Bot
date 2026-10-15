"""Metrics module: counters and latency histograms.

Tracks operational telemetry including throughput counters, error rates,
and latency percentiles (p50, p95, p99).
"""

from collections.abc import Generator
from contextlib import contextmanager
from threading import RLock
from typing import Any

from core.clock import get_clock
from core.store import MetricsRepository


class MetricsCollector:
    """Collects and aggregates counters and latency histograms."""

    def __init__(self, repo: MetricsRepository | None = None) -> None:
        self.repo = repo
        self._lock = RLock()
        self._counters: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}
        self._values: dict[str, list[float]] = {}

    def record_value(self, name: str, value: float) -> None:
        """Record a measured value such as grounding confidence."""
        with self._lock:
            self._values.setdefault(name, []).append(value)
            if self.repo:
                self.repo.record_value(name, value)

    def increment(self, name: str, value: int = 1) -> None:
        """Increment named counter."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
            if self.repo:
                self.repo.increment(name, value)

    def record_latency(self, name: str, latency_ms: float) -> None:
        """Record latency sample in milliseconds."""
        with self._lock:
            if name not in self._latencies:
                self._latencies[name] = []
            self._latencies[name].append(latency_ms)
            if self.repo:
                self.repo.record_latency(name, latency_ms)

    @contextmanager
    def time_operation(self, name: str) -> Generator[None, None, None]:
        """Context manager to measure and record block execution duration in ms."""
        clock = get_clock()
        start_time = clock.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (clock.monotonic() - start_time) * 1000.0
            self.record_latency(name, elapsed_ms)

    def get_summary(self) -> dict[str, Any]:
        """Return aggregated counters and latency histograms (p50, p95, p99)."""
        with self._lock:
            return self._summary()

    def _summary(self) -> dict[str, Any]:
        latency_summary: dict[str, dict[str, Any]] = {}
        for name, samples in self._latencies.items():
            if not samples:
                continue
            sorted_samples = sorted(samples)
            n = len(sorted_samples)

            p50 = sorted_samples[int(n * 0.50)]
            p95 = sorted_samples[min(n - 1, int(n * 0.95))]
            p99 = sorted_samples[min(n - 1, int(n * 0.99))]
            avg = sum(sorted_samples) / n

            # Histogram buckets
            buckets = [10, 50, 100, 250, 500, 1000, 2500, 5000]
            histogram = {f"le_{b}ms": sum(1 for s in sorted_samples if s <= b) for b in buckets}
            histogram["le_inf"] = n

            latency_summary[name] = {
                "count": n,
                "avg_ms": round(avg, 2),
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "histogram": histogram,
            }

        return {
            "counters": dict(self._counters),
            "latencies": latency_summary,
            "values": {name: {"count": len(values), "mean": sum(values) / len(values),
                              "latest": values[-1]} for name, values in self._values.items()},
        }

    def reset(self) -> None:
        """Reset in-memory counters and latency samples."""
        with self._lock:
            self._counters.clear()
            self._latencies.clear()
            self._values.clear()


_GLOBAL_METRICS: MetricsCollector | None = None


def set_metrics(collector: MetricsCollector | None) -> None:
    global _GLOBAL_METRICS
    _GLOBAL_METRICS = collector


def get_metrics(repo: MetricsRepository | None = None) -> MetricsCollector:
    """Return singleton MetricsCollector."""
    global _GLOBAL_METRICS
    if _GLOBAL_METRICS is None or repo is not None:
        _GLOBAL_METRICS = MetricsCollector(repo)
    return _GLOBAL_METRICS
