"""Pre-registered evaluation identity and infrastructure validity rules."""

import hashlib
import json
import os
from pathlib import Path

REGISTRATION = Path("docs/evaluation-preregistration.json")


def identity() -> dict:
    names = sorted({p.as_posix() for directory in ("core", "resources/languages", "config", "data/sample_docs")
                    for p in Path(directory).rglob("*") if p.is_file() and p.suffix in {".py", ".json", ".yaml"}}
                   | {"scripts/evaluation_support.py", "scripts/evaluate_sentiment_development.py",
                      "scripts/postfix_protocol.py", "scripts/run_postfix.py"})
    files = {name: hashlib.sha256(Path(name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in names}
    settings = {"files": files, "generation_model": os.getenv("GOOGLE_MODEL", ""), "fallback_models": []}
    digest = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    return {"config_hash": digest, **settings}


def validity(failures: int, total: int) -> dict:
    rate = failures / total if total else 1.0
    return {"infrastructure_failures": failures, "total_cases": total,
            "infrastructure_failure_rate": rate, "valid_run": rate <= .10}


def authorize_run(number: int, current_hash: str, previous: dict | None) -> None:
    if number == 1:
        return
    if number != 2 or not previous or previous.get("config_hash") != current_hash:
        raise ValueError("Only one rerun with an identical registered config hash is permitted")
    if previous.get("infrastructure_failure_rate", 0) <= .10:
        raise ValueError("A rerun requires more than 10% infrastructure failures in the prior run")


def register() -> dict:
    if REGISTRATION.exists():
        raise ValueError("Pre-registration already exists; do not overwrite after evaluation")
    report = {**identity(), "rule": "More than 10% provider infrastructure failures invalidates a run; one rerun only, identical config hash",
              "failure_definition": "A case with terminal provider quota/transport/timeout/auth/config failure or incomplete embedding coverage. Count cases, not retries. Semantic refusals, confidence/schema rejection and safety blocks are not infrastructure failures.",
              "denominator": "All pre-registered cases; require every case completed. Incomplete runs are retained and cannot be declared valid.",
              "cache_rule": "Successful immutable model/content-keyed vectors may be reused; no invented vectors. Classification sessions are unique per case and run.",
              "prior_exposure": {"T4": "Pre-fix 3/20 (15.00%) answered/correct cited, 0/52 false; prior run already exposed",
                                 "T5": "Pre-fix 22/48 (45.83%) pipeline, six accepted provider decisions; earlier JSON-format diagnostic run also retained"},
              "protocol": "Freeze source and config before any post-fix held-out evaluation. No tuning from post-fix outcomes. Run 2 allowed only if run 1 exceeds the failure threshold; report all runs.",
              "translation": "Separate synthetic en-to-hi/te/es probe after held-out evaluations; report real success only with verified entity bytes and actual provider response.",
              "contract_tests": "Existing offline scripted-vector held-out contract tests remain; they are not live evaluation runs or calibration data."}
    REGISTRATION.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def verify() -> str:
    registered = json.loads(REGISTRATION.read_text())
    if identity()["config_hash"] != registered["config_hash"]:
        raise ValueError("Registered evaluation configuration or implementation changed")
    return registered["config_hash"]
