"""Development diagnostics only: never reads the frozen held-out data."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clock import FakeClock, set_global_clock  # noqa: E402
from core.embeddings import document_text  # noqa: E402
from core.llm import FakeLLM  # noqa: E402
from core.retrieval import PolicyRetrievalEngine  # noqa: E402
from core.store import DocumentRepository  # noqa: E402
from scripts.evaluation_support import EvaluationVectors, PacedProvider, wilson  # noqa: E402


def evaluate(live: bool, output: Path) -> dict:
    path = Path("tests/fixtures/task4/dev/cases.json")
    corpus = json.loads(path.read_text(encoding="utf-8"))
    set_global_clock(FakeClock(corpus["clock"]))
    provider = PacedProvider() if live else None
    engine = PolicyRetrievalEngine(DocumentRepository(), provider or FakeLLM())
    for doc in json.loads((path.parent / corpus["documents"]).read_text(encoding="utf-8")):
        engine.ingest_document(doc)
    if provider:
        vectors = EvaluationVectors(provider, Path(".verification/dev4-vectors.json"))
        vectors.warm([document_text(d) for d in engine.repo.list_all() if not d.is_injected], "RETRIEVAL_DOCUMENT")
        vectors.warm([c["question"] for c in corpus["cases"]], "RETRIEVAL_QUERY")
        engine.embedder = vectors
        engine.reindex()
    outcomes = []
    for case in corpus["cases"]:
        try:
            result = engine.query(case["question"], case["role"], case.get("as_of"), case.get("product"), case.get("region"))
            answered = not result.refusal and not result.clarification_needed
            correct = (answered and result.verified and any(c["doc_id"] == case["expected_doc_id"] for c in result.citations)
                       and (case["expected_fact"] is None or case["expected_fact"].lower() in result.answer.lower()))
            outcome = {"id": case["id"], "scenario": case["scenario"], "expected_refusal": case["expected_refusal"],
                       "answered": answered, "correct": correct, "false_answer": answered and (case["expected_refusal"] or not correct),
                       "answer": result.answer, "trace": result.trace}
        except (RuntimeError, ValueError, OSError) as exc:
            outcome = {"id": case["id"], "scenario": case["scenario"], "expected_refusal": case["expected_refusal"],
                       "answered": False, "correct": False, "false_answer": False,
                       "error": type(exc).__name__, "trace": engine.diagnostic_trace}
        outcomes.append(outcome)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"progress": len(outcomes), "outcomes": outcomes}, ensure_ascii=False, indent=2), encoding="utf-8")
    positive = [o for o in outcomes if not o["expected_refusal"]]
    negative = [o for o in outcomes if o["expected_refusal"]]
    report = {"scope": "Actual provider with cached measured embeddings" if live else "Offline lexical / deterministic extraction; not provider accuracy",
              "dev_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "document_count": engine.repo.count(),
              "answer_rate": wilson(sum(o["answered"] for o in positive), len(positive)),
              "correct_cited_rate": wilson(sum(o["correct"] for o in positive), len(positive)),
              "false_answer_rate": wilson(sum(o["false_answer"] for o in negative), len(negative)),
              "decisions": dict(Counter(o["trace"].get("decision") for o in outcomes)),
              "embedding_fallback_cases": sum(bool(o["trace"].get("embedding_fallback")) for o in outcomes),
              "embedding_batch_errors": vectors.errors if provider else [], "outcomes": outcomes}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    engine.repo.close()
    return {key: value for key, value in report.items() if key != "outcomes"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.live:
        from dotenv import load_dotenv
        load_dotenv()
    print(json.dumps(evaluate(args.live, args.output), indent=2))
