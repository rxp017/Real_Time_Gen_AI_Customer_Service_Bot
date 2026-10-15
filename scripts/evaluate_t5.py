"""Measure classifier accuracy exclusively on the authored labelled dataset."""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.sentiment import SentimentClassifier  # noqa: E402


def evaluate() -> dict:
    path = Path("tests/fixtures/task5/labelled_sentiment.json")
    raw = path.read_bytes()
    corpus = json.loads(raw)
    classifier = SentimentClassifier()
    languages, confusion, failures = {}, {}, []
    correct = 0
    ids = set()
    labels = {"positive", "neutral", "negative", "frustrated", "urgent", "sarcastic"}
    for row in corpus["examples"]:
        if row["id"] in ids or row["label"] not in labels:
            raise ValueError("Dataset requires unique ids and valid labels")
        ids.add(row["id"])
        prediction = classifier.classify(row["message"], row["history"])
        matched = prediction.label == row["label"]
        correct += int(matched)
        count = languages.setdefault(row["language"], {"correct": 0, "total": 0})
        count["correct"] += int(matched)
        count["total"] += 1
        cell = confusion.setdefault(row["label"], Counter())
        cell[prediction.label] += 1
        if not matched:
            failures.append({"id": row["id"], "expected": row["label"], "predicted": prediction.label,
                             "message": row["message"]})
    return {"dataset": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "scope": "Authored diagnostic set only; not independently blinded or production accuracy",
            "correct": correct, "total": len(ids), "accuracy": correct / len(ids),
            "languages": languages, "confusion": confusion, "failures": failures}


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
