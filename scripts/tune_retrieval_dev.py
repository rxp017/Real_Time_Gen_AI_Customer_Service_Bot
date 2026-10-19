"""Select a zero-false-answer dev configuration; never opens held-out files."""

import itertools
import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import retrieval  # noqa: E402
from core.clock import FakeClock, set_global_clock  # noqa: E402
from core.config import get_config_manager  # noqa: E402
from core.llm import FakeLLM  # noqa: E402
from core.retrieval import PolicyRetrievalEngine  # noqa: E402
from core.store import DocumentRepository  # noqa: E402
from scripts.evaluation_support import EvaluationVectors, PacedProvider  # noqa: E402


def tune() -> dict:
    corpus = json.loads(Path("tests/fixtures/task4/dev/cases.json").read_text())
    set_global_clock(FakeClock(corpus["clock"]))
    vectors = EvaluationVectors(PacedProvider(), Path(".verification/dev4-vectors.json"))
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM(), embedder=vectors)
    for doc in json.loads(Path("tests/fixtures/task4/dev/documents.json").read_text()):
        engine.ingest_document(doc)
    # Immutable dev corpus: memoization changes cost, not the computed values.
    engine.repo.load_vector = lru_cache(maxsize=None)(engine.repo.load_vector)
    engine.searcher.compute_similarity = lru_cache(maxsize=None)(engine.searcher.compute_similarity)
    current_case = [""]
    native_cosine = retrieval.cosine
    measured_scores = {}
    def memoized_cosine(first, second):
        key = (current_case[0], id(second))
        if key not in measured_scores:
            measured_scores[key] = native_cosine(first, second)
        return measured_scores[key]
    retrieval.cosine = memoized_cosine
    rows = []
    manager = get_config_manager()
    for lexical, coverage, semantic_override in itertools.product((.4, .45, .55), (0.0, .4), (.88,)):
        hybrid, weight, margin = .5, .2, .08
        settings = {"thresholds.similarity_threshold": lexical, "retrieval.hybrid_threshold": hybrid,
                    "retrieval.lexical_weight": weight, "retrieval.semantic_weight": 1 - weight,
                    "retrieval.minimum_rank_margin": margin}
        settings.update({"retrieval.minimum_query_coverage": coverage, "retrieval.semantic_override": semantic_override})
        for key, value in settings.items():
            manager.update_runtime_override(key, value)
        correct = false = answered = missing = 0
        for case in corpus["cases"]:
            current_case[0] = case["id"]
            result = engine.query(case["question"], case["role"], case.get("as_of"), case.get("product"), case.get("region"))
            accepted = not result.refusal and not result.clarification_needed
            supported = accepted and result.verified and any(c["doc_id"] == case["expected_doc_id"] for c in result.citations)
            correct += bool(supported and case["expected_fact"] and case["expected_fact"].lower() in result.answer.lower())
            answered += accepted and not case["expected_refusal"]
            false += accepted and (case["expected_refusal"] or not supported)
            missing += bool(result.trace.get("embedding_fallback"))
        rows.append({"settings": settings, "correct": correct, "answered": answered, "false_answers": false,
                     "embedding_fallback_cases": missing})
    candidates = [r for r in rows if r["false_answers"] == 0]
    selected = max(candidates, key=lambda r: (r["correct"], r["settings"]["retrieval.hybrid_threshold"],
                                             r["settings"]["retrieval.minimum_rank_margin"])) if candidates else None
    report = {"scope": "Dev-only measured-vector replay and deterministic quote generation; not live accuracy",
              "candidate_count": len(rows), "selected": selected, "candidates": rows}
    Path("docs/verification/revision-t4-dev-final-tuning.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"candidate_count": len(rows), "selected": selected}, indent=2))
    return report


if __name__ == "__main__":
    tune()
