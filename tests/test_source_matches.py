"""Quote existence is transparent; semantic and independent truth remain open."""
import pytest
from pydantic import ValidationError

from src.schema import DealExtraction, DealRecord, EvidenceExcerpt
from src.scoring import apply_vc_scorecard


def test_matching_source_quote_is_not_equated_with_fact_verification():
    record = DealRecord(evidence_excerpts=[
        EvidenceExcerpt(
            category="Traction",
            claim="ARR grew 20%",
            quote="ARR declined 20%",
        )
    ])
    analyzed = apply_vc_scorecard(record, "ARR declined 20% in the period.")
    assert len(analyzed.source_matches) == 1
    match = analyzed.source_matches[0]
    assert match.exact_text_match is True
    assert match.review_status == "Quote found — assess claim support"


def test_invented_quote_is_flagged():
    record = DealRecord(evidence_excerpts=[
        EvidenceExcerpt(
            category="Traction",
            claim="ARR grew 200%",
            quote="Revenue grew 200% year over year.",
        )
    ])
    analyzed = apply_vc_scorecard(record, "No revenue information was disclosed.")
    assert analyzed.source_matches[0].exact_text_match is False
    assert "Quote not found" in analyzed.source_matches[0].review_status


def test_ai_cannot_set_application_owned_match_status():
    with pytest.raises(ValidationError):
        DealExtraction(company_name="Example", source_matches=[
            {"category": "Traction", "claim": "Fake", "quote": "Fake",
             "exact_text_match": True}
        ])
    with pytest.raises(ValidationError):
        EvidenceExcerpt(
            category="Traction", claim="Claim", quote="Quote",
            exact_text_match=True,
        )
