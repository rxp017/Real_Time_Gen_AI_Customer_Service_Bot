"""Recorded actual dev vectors and deterministic generation are a regression, not live accuracy."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from core.clock import FakeClock, set_global_clock
from core.llm import FakeLLM
from core.retrieval import PolicyRetrievalEngine
from core.store import DocumentRepository
from scripts.evaluation_support import EvaluationVectors, PacedProvider


def test_dev_lookalikes_zero_false_answers_with_one_hundred_distractors(tmp_path):
    manifest = json.loads(Path("docs/verification/revision-dev-vector-manifest.json").read_text())
    assert hashlib.sha256(Path("docs/verification/revision-dev-vectors.json.gz").read_bytes()).hexdigest() == manifest["sha256"]
    cases = json.loads(Path("tests/fixtures/task4/dev/cases.json").read_text())
    documents = json.loads(Path("tests/fixtures/task4/dev/documents.json").read_text())
    assert sum(d["doc_id"].startswith("DEV-DISTRACTOR-") for d in documents) == 100
    set_global_clock(FakeClock(cases["clock"]))
    vectors = EvaluationVectors(PacedProvider(), tmp_path / "unused.json")
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM(), embedder=vectors)
    for doc in documents:
        engine.ingest_document(doc)
    engine.repo.load_vector = lru_cache(maxsize=None)(engine.repo.load_vector)
    for case in cases["cases"]:
        result = engine.query(case["question"], case["role"], case.get("as_of"), case.get("product"), case.get("region"))
        assert not result.trace.get("embedding_fallback")
        if case["expected_refusal"]:
            assert result.refusal or result.clarification_needed, case["id"]
        else:
            assert result.verified and not result.refusal and not result.clarification_needed, case["id"]
            assert any(c["doc_id"] == case["expected_doc_id"] for c in result.citations)
            assert case["expected_fact"].lower() in result.answer.lower()
