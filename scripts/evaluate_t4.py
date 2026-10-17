"""Evaluate frozen paraphrases, distinguishing lexical/fake and actual live-provider runs."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clock import FakeClock, SystemClock, set_global_clock  # noqa: E402
from core.llm import FakeLLM, RealProviderAdapter  # noqa: E402
from core.retrieval import PolicyRetrievalEngine  # noqa: E402
from core.store import DocumentRepository  # noqa: E402


def evaluate(live: bool = False) -> dict:
    path = Path("tests/fixtures/task4/heldout_paraphrases.json")
    raw = path.read_bytes()
    expected = path.with_suffix(".sha256").read_text().strip()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Frozen held-out corpus bytes changed")
    data = json.loads(raw)
    set_global_clock(FakeClock(data["clock"]))
    provider = RealProviderAdapter(fallback_models=[], clock=SystemClock()) if live else FakeLLM()
    engine = PolicyRetrievalEngine(DocumentRepository(), provider)
    engine.load_fixture_directory("data/sample_docs")
    outcomes = []
    for case in data["cases"]:
        try:
            result = engine.query(case["question"], case["role"])
            answered = not result.refusal and not result.clarification_needed and result.verified
            correct = answered and any(c["doc_id"] == case["expected_doc_id"] for c in result.citations)
            outcomes.append({"id": case["id"], "answerable": not case["expected_refusal"],
                             "answered": answered, "correct_cited_answer": correct,
                             "false_answer": answered and (case["expected_refusal"] or not correct),
                             "answer": result.answer, "citations": result.citations})
        except (RuntimeError, ValueError, OSError) as exc:
            outcomes.append({"id": case["id"], "answerable": not case["expected_refusal"],
                             "answered": False, "correct_cited_answer": False, "false_answer": False,
                             "error": type(exc).__name__})
    positive = [r for r in outcomes if r["answerable"]]
    negative = [r for r in outcomes if not r["answerable"]]
    report = {"scope": "Actual provider" if live else "Offline lexical retrieval with extractive FakeLLM; not provider accuracy",
              "corpus_sha256": expected, "model": getattr(provider, "model", "FakeLLM"),
              "embedding_model": getattr(engine.embedder, "embedding_model", None),
              "answerable_cases": len(positive), "unanswerable_cases": len(negative),
              "answer_rate": sum(r["answered"] for r in positive) / len(positive),
              "correct_cited_answer_rate": sum(r["correct_cited_answer"] for r in positive) / len(positive),
              "false_answer_rate": sum(r["false_answer"] for r in negative) / len(negative),
              "embedding_failures": engine.embedding_failures, "errors": sum("error" in r for r in outcomes),
              "outcomes": outcomes}
    engine.repo.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        from dotenv import load_dotenv
        load_dotenv()
    print(json.dumps(evaluate(args.live), indent=2, ensure_ascii=False))
