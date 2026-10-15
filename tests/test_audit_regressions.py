"""Audit reproductions for claims not covered by the original acceptance fixtures."""

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from core.audit import AuditLogger
from core.clock import FakeClock, set_global_clock
from core.conversation import ConversationService
from core.ingestion import InvalidFile, read_policy
from core.llm import FakeLLM
from core.metrics import MetricsCollector
from core.retrieval import PolicyRetrievalEngine, SemanticSearcher
from core.risk import HighRiskDetector
from core.sessions import SessionManager
from core.store import Document, DocumentRepository, SessionRepository
from core.upload_gate import UploadGate, UploadRejected


def test_audit_truncated_policy_condition_is_not_supported() -> None:
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    try:
        assert not engine.verify_claim("Refunds are available.",
                                       "Refunds are available only if proof of purchase is provided.")
        assert not engine.verify_claim("Refunds are available.", "It is not true that refunds are available.")
    finally:
        engine.repo.close()


def test_audit_multiple_regions_cannot_be_resolved_by_similarity_alone() -> None:
    class Scores(SemanticSearcher):
        def compute_similarity(self, query: str, document_text: str) -> float:
            return 0.99 if "14 days" in document_text else 0.75

    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM(), Scores())
    set_global_clock(FakeClock())
    try:
        for doc_id, region, days in (("IN", "IN", 14), ("US", "US", 30)):
            engine.ingest_document(Document(doc_id, 1, "bootcamp", region, "public", "2020-01-01", None,
                                             "refund", "Refund policy", f"Refunds are available within {days} days."))
        assert engine.query("What is the refund policy?").clarification_needed
    finally:
        engine.repo.close()


def test_audit_rag_clarification_survives_orchestrator(tmp_path: Path) -> None:
    clock = FakeClock()
    set_global_clock(clock)
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    engine.load_fixture_directory("data/sample_docs")
    conversation = ConversationService(SessionManager(SessionRepository(str(tmp_path / "sessions.db")), clock),
                                       AuditLogger(), MetricsCollector())
    try:
        result = conversation.turn("When will mentorship course materials be delivered?", "audit", "owner",
                                   lambda query: engine.query(query, "customer"))
        assert "clarify" in result.answer.casefold()
        assert result.clarification_needed
    finally:
        conversation.sessions.repo.close()
        conversation.support.repo.close()
        conversation.tickets.repo.close()
        engine.repo.close()


def test_audit_negated_old_issue_does_not_hide_current_high_risk() -> None:
    assert HighRiskDetector().detect("I was not charged twice last month; today I was charged twice.") == ["duplicate_payment"]
    assert HighRiskDetector().detect("I was not charged twice.") == []


def test_audit_year_only_question_does_not_invent_a_date() -> None:
    set_global_clock(FakeClock())
    engine = PolicyRetrievalEngine(DocumentRepository(), FakeLLM())
    try:
        for name, version, start, expiry, days in (("EARLY", 1, "2024-01-01", "2024-07-01", 14),
                                                  ("LATE", 2, "2024-07-01", None, 30)):
            engine.ingest_document(Document(name, version, "bootcamp", "IN", "public", start, expiry,
                                             "refund", "2024 Refund policy", f"Refunds are available within {days} days."))
        result = engine.query("What was the refund policy in 2024?")
        assert result.clarification_needed and not result.citations
        explicit = engine.query("What was the refund policy in 2024?", as_of="2024-08-01")
        assert explicit.verified and "30 days" in explicit.answer
    finally:
        engine.repo.close()


def test_audit_pdf_jpeg_expansion_is_aggregated_before_decoding() -> None:
    image = Image.new("RGB", (3000, 3000), "white")
    pdf = io.BytesIO()
    try:
        image.save(pdf, format="PDF", save_all=True, append_images=[image], resolution=150)
    finally:
        image.close()
    with pytest.raises(UploadRejected, match="decompression_limit"):
        UploadGate(AuditLogger()).validate(pdf.getvalue(), "aggregate.pdf", "application/pdf")


@pytest.mark.parametrize("effective,expiry,valid", [
    ("2026-01-01T23:00:00+00:00", "2026-01-02T00:00:00+05:30", False),
    ("2026-01-02T00:00:00+05:30", "2026-01-01T23:00:00+00:00", True),
])
def test_audit_policy_validity_compares_instants(effective: str, expiry: str, valid: bool, tmp_path: Path) -> None:
    policy = json.loads(Path("data/sample_docs/policy_v2_refund.json").read_text(encoding="utf-8"))
    policy.update(effective_date=effective, expiry_date=expiry)
    path = tmp_path / "offsets.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    if valid:
        assert read_policy(path)[0]["effective_date"] == effective
    else:
        with pytest.raises(InvalidFile, match="corrupt"):
            read_policy(path)
