"""Evaluate the independently committed new labels without modifying resources."""

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clock import SystemClock  # noqa: E402
from core.config import get_config_manager  # noqa: E402
from core.llm import RealProviderAdapter  # noqa: E402
from core.risk import HighRiskDetector  # noqa: E402
from core.sentiment import SentimentClassifier  # noqa: E402


def evaluate(live: bool) -> dict:
    path = Path("tests/fixtures/task5/heldout_sentiment.json")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != path.with_suffix(".sha256").read_text().strip():
        raise ValueError("Frozen sentiment corpus changed")
    cases = json.loads(raw)["examples"]
    get_config_manager().update_runtime_override("support.llm_classification", live)
    provider = RealProviderAdapter(fallback_models=[], clock=SystemClock()) if live else None
    classifier = SentimentClassifier(provider=provider)
    def run(case):
        prediction = classifier.classify(case["message"], case["history"])
        return {"id": case["id"], "language": case["language"], "expected": case["label"],
                "predicted": prediction.label, "confidence": prediction.confidence,
                "correct": prediction.label == case["label"], "evidence": prediction.evidence,
                "expected_risk": case["high_risk"], "detected_risk": HighRiskDetector().detect(case["message"])}
    with ThreadPoolExecutor(max_workers=2 if live else 1) as executor:
        outcomes = list(executor.map(run, cases))
    return {"scope": "Actual LLM-assisted pipeline including reported pattern fallbacks" if live else "Pattern-only baseline",
            "corpus_sha256": digest, "total": len(outcomes), "correct": sum(r["correct"] for r in outcomes),
            "accuracy": sum(r["correct"] for r in outcomes) / len(outcomes),
            "provider_classifications": sum(any(e.startswith("provider:") for e in r["evidence"]) for r in outcomes),
            "outcomes": outcomes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        from dotenv import load_dotenv
        load_dotenv()
    print(json.dumps(evaluate(args.live), ensure_ascii=False, indent=2))
