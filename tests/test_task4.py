"""Evaluation tests for Task 4: Policy & Knowledge Retrieval Engine.

Implements all 10 required evaluation scenario tests exactly as named in docs/tasks/T4.md:
- test_conflicting_policies_latest_wins
- test_restricted_doc_not_retrieved
- test_expired_policy_ignored_for_current
- test_future_dated_ignored_for_current
- test_historical_question_uses_policy_active_on_date
- test_citation_present_on_every_factual_answer
- test_refuses_when_no_evidence
- test_ambiguous_asks_clarification
- test_unsupported_claim_detected
- test_prompt_injected_doc_ignored
"""

from pathlib import Path

import pytest

from core.clock import FakeClock, set_global_clock
from core.llm import FakeLLM
from core.retrieval import PolicyRetrievalEngine
from core.store import DocumentRepository

FIXTURES_DIR = Path("data/sample_docs")


@pytest.fixture
def test_engine() -> PolicyRetrievalEngine:
    """Fixture providing isolated in-memory DocumentRepository and FakeClock."""
    # Set deterministic test clock to current date: 2026-10-13
    fake_clock = FakeClock("2026-10-13T12:00:00+05:30")
    set_global_clock(fake_clock)

    repo = DocumentRepository(":memory:")
    fake_llm = FakeLLM()
    engine = PolicyRetrievalEngine(repo=repo, llm=fake_llm)
    engine.load_fixture_directory(FIXTURES_DIR)
    return engine


def test_conflicting_policies_latest_wins(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: within a doc_family+product+region keep the latest applicable version."""
    query = "What is the refund policy for bootcamp?"
    results = test_engine.retrieve(query, caller_role="customer")

    # Both v1 (50%) and v2 (100%) exist, but only v2 should survive Stage 4 conflict resolution
    matching_refund_docs = [r.document for r in results if r.document.doc_family == "fam_refund"]
    assert len(matching_refund_docs) == 1
    winner = matching_refund_docs[0]
    assert winner.doc_id == "DOC-REFUND-V2"
    assert winner.version == 2
    assert "100% full refund" in winner.content


def test_restricted_doc_not_retrieved(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: (1) authorise by caller role. Filtering happens BEFORE search."""
    query = "Tell me about agent escalation workflow for customer refunds"

    # Public user should NOT retrieve the support_agent internal SOP
    public_results = test_engine.retrieve(query, caller_role="public")
    sop_in_public = [r.document for r in public_results if r.document.doc_id == "DOC-SOP-ADMIN"]
    assert len(sop_in_public) == 0

    # Support agent user MUST retrieve the support_agent internal SOP
    agent_results = test_engine.retrieve(query, caller_role="support_agent")
    sop_in_agent = [r.document for r in agent_results if r.document.doc_id == "DOC-SOP-ADMIN"]
    assert len(sop_in_agent) == 1
    assert sop_in_agent[0].doc_id == "DOC-SOP-ADMIN"


def test_expired_policy_ignored_for_current(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: ignore expired policies for current questions."""
    query = "What seasonal discount promotion is available for data science bootcamp?"
    results = test_engine.retrieve(query, caller_role="customer")

    # DOC-DISCOUNT-EXPIRED expired on 2025-12-31; current fake clock is in 2026
    expired_matches = [r.document for r in results if r.document.doc_id == "DOC-DISCOUNT-EXPIRED"]
    assert len(expired_matches) == 0


def test_future_dated_ignored_for_current(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: ignore future-dated policies for current questions."""
    query = "What are the laptop hardware requirements?"
    results = test_engine.retrieve(query, caller_role="customer")

    # DOC-HARDWARE-FUTURE is effective in 2027; current fake clock is in 2026
    future_matches = [r.document for r in results if r.document.doc_id == "DOC-HARDWARE-FUTURE"]
    assert len(future_matches) == 0


def test_historical_question_uses_policy_active_on_date(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: if the question names a past date, parse it and use it."""
    query = "What were the laptop standards in 2024?"
    results = test_engine.retrieve(query, caller_role="customer")

    historical_matches = [r.document for r in results if r.document.doc_id == "DOC-LAPTOP-2024"]
    assert len(historical_matches) == 1
    assert "4GB RAM was standard" in historical_matches[0].content


def test_citation_present_on_every_factual_answer(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: each answer cites source (doc id, version, section)."""
    query = "What is the refund policy for bootcamp?"
    result = test_engine.query(query, caller_role="customer")

    assert result.refusal is False
    assert len(result.citations) >= 1
    citation = result.citations[0]
    assert citation["doc_id"] == "DOC-REFUND-V2"
    assert citation["version"] == 2
    assert citation["section"] == "Refund Policy"
    # Source cite formatted directly in answer text
    assert "[DOC-REFUND-V2, v2, Refund Policy]" in result.answer


def test_refuses_when_no_evidence(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: No evidence -> refuse (never guess)."""
    query = "What is the policy for astronaut training and rocket missions?"
    result = test_engine.query(query, caller_role="customer")

    assert result.refusal is True
    assert "no relevant policy or documentation was found" in result.answer.lower()
    assert len(result.citations) == 0


def test_ambiguous_asks_clarification(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: ambiguous evidence -> ask a clarifying question (never guess)."""
    query = "When will mentorship course materials be delivered?"
    result = test_engine.query(query, caller_role="customer")

    assert result.clarification_needed is True
    assert "clarify" in result.answer.lower()
    assert len(result.citations) == 2


def test_unsupported_claim_detected(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: Post-generation verifier checks every claim sentence is supported by cited chunk."""
    # 1. Direct unit verification check
    grounded_claim = "Learners are eligible for a 100% full refund within 14 days of course enrollment."
    unsupported_claim = "Learners will receive a free Tesla sports car and 500% bonus cashback."
    source_content = "Learners are eligible for a 100% full refund within 14 days of course enrollment."

    assert test_engine.verify_claim(grounded_claim, source_content) is True
    assert test_engine.verify_claim("Learners are eligible for a 100% full refund within 14 days.", source_content) is False
    assert test_engine.verify_claim(unsupported_claim, source_content) is False

    # 2. Pipeline integration with LLM returning unsupported hallucination
    hallucinating_llm = FakeLLM(
        default_response="Students will receive free BMW luxury vehicles. [DOC-REFUND-V2, v2, Refund Policy]"
    )
    engine_with_hallucination = PolicyRetrievalEngine(repo=test_engine.repo, llm=hallucinating_llm)
    gen_result = engine_with_hallucination.query("What is the refund policy?", caller_role="customer")

    assert gen_result.verified is False
    assert gen_result.refusal is True
    assert "unsupported by verified documentation" in gen_result.answer


def test_prompt_injected_doc_ignored(test_engine: PolicyRetrievalEngine) -> None:
    """Requirement: Documents are untrusted: run injection detector; flagged instructions neutralised."""
    injected_doc = test_engine.repo.get_document("DOC-ADVERSARIAL-01")
    assert injected_doc is not None
    assert injected_doc.is_injected is True
    assert "[NEUTRALIZED_INSTRUCTION:" in injected_doc.content

    # If queried, the prompt injection instruction is defanged
    query = "What is the administrative override notice?"
    result = test_engine.query(query, caller_role="customer")
    assert "admin password" not in result.answer.lower() or "[neutralized" in result.answer.lower()
