"""Diagnostic scores describe only authorized survivors and never change decisions."""

from core.llm import FakeLLM
from tests.test_hybrid import hybrid


def test_trace_scores_only_survivors_with_components_and_rank():
    engine, vectors = hybrid()
    question = "bootcamp refund"
    vectors.vectors[question] = [1, 0]
    result = engine.query(question, "public")
    trace = result.trace
    filtered = {item["doc_id"] for item in trace["filters"]}
    assert not filtered & {item["doc_id"] for item in trace["scores"]}
    assert "DOC-SOP-ADMIN" in filtered
    for item in trace["scores"]:
        assert item["embedding"] is not None and item["rank"] >= 1
        assert abs(item["fused"] - (.65 * item["embedding"] + .35 * item["lexical"])) < 1e-9
        assert item["threshold_pass"] == (item["fused"] >= item["threshold"])


def test_trace_distinguishes_threshold_verifier_and_embedding_fallback():
    engine, vectors = hybrid()
    vectors.unavailable = True
    result = engine.query("bootcamp refund policy", "customer")
    assert result.trace["embedding_fallback"] == "query_embedding_failure"
    assert engine.query("submarine archaeology expedition", "customer").trace["decision"] == "threshold"
    engine.llm = FakeLLM(default_response="Invented secret benefit. [DOC-REFUND-V2, v2, Refund Policy]")
    assert engine.query("bootcamp refund policy", "customer").trace["decision"] == "grounding_verifier"
