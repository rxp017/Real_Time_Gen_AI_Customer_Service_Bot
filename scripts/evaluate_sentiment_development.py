"""Evaluate only the new sentiment development labels, with separate fallback accounting."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import get_config_manager  # noqa: E402
from core.risk import HighRiskDetector  # noqa: E402
from core.sentiment import SentimentClassifier  # noqa: E402
from scripts.evaluation_support import PacedProvider, wilson  # noqa: E402


def measure(cases: list[dict], live: bool, output: Path, digest: str, session_namespace: str = "development") -> dict:
    get_config_manager().update_runtime_override("support.llm_classification", live)
    classifier = SentimentClassifier(provider=PacedProvider() if live else None)
    outcomes = []
    for case in cases:
        prediction = classifier.classify(case["message"], case["history"], session_id=f"{session_namespace}:{case['id']}")
        outcomes.append({"id": case["id"], "language": case["language"], "label": case["label"],
                         "predicted": prediction.label, "correct": prediction.label == case["label"],
                         "confidence": prediction.confidence, "provider_status": prediction.provider_status,
                         "provider_attempts": prediction.provider_attempts,
                         "expected_risk": case["high_risk"], "risk": HighRiskDetector().detect(case["message"])})
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"progress": len(outcomes), "outcomes": outcomes}, ensure_ascii=False, indent=2), encoding="utf-8")
    assisted = [o for o in outcomes if o["provider_status"] in {"accepted", "cache_hit"}]
    fallback = [o for o in outcomes if o not in assisted]
    report = {"scope": "Actual provider pipeline with individually identified fallbacks" if live else "Pattern-only development baseline",
              "corpus_sha256": digest, "pipeline": wilson(sum(o["correct"] for o in outcomes), len(outcomes)),
              "model_assisted": wilson(sum(o["correct"] for o in assisted), len(assisted)),
              "fallback": wilson(sum(o["correct"] for o in fallback), len(fallback)),
              "provider_status_counts": dict(Counter(o["provider_status"] for o in outcomes)),
              "outcomes": outcomes}
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return {k: v for k, v in report.items() if k != "outcomes"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.live:
        from dotenv import load_dotenv
        load_dotenv()
    path = Path("tests/fixtures/task5/dev_sentiment.json")
    print(json.dumps(measure(json.loads(path.read_text(encoding="utf-8"))["examples"], args.live,
                             args.output, hashlib.sha256(path.read_bytes()).hexdigest()), indent=2))
