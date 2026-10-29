"""Adversarial regression cases for portfolio evidence quality."""
from src.demo import curated_northstar_example
from src.intake import source_notes_for_analysis
from src.sample_data import DEFAULT_SAMPLE_DEAL_NOTES
from src.schema import DealRecord, DiligenceScorecardItem
from src.scoring import _has_any, apply_vc_scorecard, fallback_deal_record
from src.ui.components import scorecard_dataframe


def test_missing_disclosures_do_not_score_as_evidence():
    notes = (
        "No founder background or management team information was provided. "
        "No TAM or market size estimates were disclosed. "
        "No pricing, CAC, or business model details are available. "
        "No GTM, pipeline, distribution, or sales channels were supplied. "
        "No competitor or regulatory risk evidence is available."
    )
    record = apply_vc_scorecard(DealRecord(), notes)
    assert record.opportunity_score == 0
    assert all(item.score == 0 for item in record.diligence_scorecard)


def test_keyword_stuffing_without_disclosures_does_not_score():
    notes = (
        "founder, CEO, operator, background, TAM, market size, why now, "
        "workflow, differentiation, pricing, CAC, LTV, GTM, pipeline, "
        "competitor, moat, churn, concentration, retention."
    )
    record = apply_vc_scorecard(DealRecord(), notes)
    assert record.opportunity_score == 0


def test_substring_collisions_do_not_match():
    notes = "A company based in Amsterdam sells cacao around Europe."
    assert not _has_any(notes, ["tam"])
    assert not _has_any(notes, ["cac"])
    assert not _has_any(notes, ["operator"])


def test_negative_actual_performance_is_not_treated_as_missing():
    record = DealRecord(
        traction_signals=["ARR declined 20%", "Customer retention fell to 70%"],
        customer_signals=["Enterprise buyers"],
    )
    scored = apply_vc_scorecard(
        record, "ARR declined 20% year over year. Customer retention fell to 70%."
    )
    row = next(x for x in scored.diligence_scorecard if "Traction" in x.category)
    assert row.score >= 8


def test_source_metadata_does_not_enter_evidence_notes():
    notes = "Builds software for clinics."
    a = source_notes_for_analysis(
        notes, company_name="Sample", source_type="Founder call notes"
    )
    b = source_notes_for_analysis(
        notes, company_name="Sample", source_type="Website text",
        investment_focus="Founders and business model"
    )
    assert a == b == notes
    assert apply_vc_scorecard(DealRecord(), a).opportunity_score == (
        apply_vc_scorecard(DealRecord(), b).opportunity_score
    )


def test_fallback_is_unscored_and_contains_no_invented_business_claims():
    record = fallback_deal_record(
        "Company: Northstar\nFounder has strong experience and product traction."
    )
    assert record.fallback_used
    assert record.priority == "Not analyzed"
    assert record.opportunity_score == 0
    assert record.confidence_score == 0
    assert record.diligence_scorecard == []
    assert record.description == "Unknown"
    assert record.risks == []


def test_fictional_offline_demo_is_marked_curated_and_has_evidence():
    record = curated_northstar_example(DEFAULT_SAMPLE_DEAL_NOTES)
    assert not record.fallback_used
    assert record.analysis_path == "curated_offline_demo"
    assert record.model_name == "none"
    assert "No AI extraction" in record.analysis_warning
    assert 0 < record.opportunity_score <= 100


def test_progress_bar_uses_category_specific_maximum():
    table = scorecard_dataframe(
        [DiligenceScorecardItem(category="Risk Evidence", score=5, max_score=5)]
    )
    assert table.loc[0, "Coverage %"] == 100
