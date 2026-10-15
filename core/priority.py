"""Configurable, bounded ticket priority with auditable component scores."""

import math
from typing import Any

from core.config import get_config


def priority_score(severity: str, sentiment: str, waiting_minutes: float,
                   impact: str, sla_ratio: float) -> dict[str, Any]:
    cfg = get_config().get("tickets.priority")
    weights = cfg["weights"]
    if any(not math.isfinite(float(w)) or float(w) < 0 for w in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("Priority weights must be finite, nonnegative and have a positive sum")
    cap = float(cfg["waiting_cap_minutes"])
    if cap <= 0 or not all(math.isfinite(v) for v in (waiting_minutes, sla_ratio)):
        raise ValueError("Invalid priority inputs")
    values = {"severity": float(cfg["severity"][severity]), "sentiment": float(cfg["sentiment"][sentiment]),
              "waiting": min(1.0, max(0.0, waiting_minutes / cap)), "impact": float(cfg["impact"][impact]),
              "sla": min(1.0, max(0.0, sla_ratio))}
    if any(not 0 <= v <= 1 for v in values.values()):
        raise ValueError("Priority components must be within [0,1]")
    score = 100 * sum(values[k] * weights[k] for k in values) / sum(weights.values())
    return {"score": round(score, 6), "components": values, "weights": dict(weights)}
