"""Extracted signals earn evidence credit only when the source notes back them."""
from src.schema import DealRecord
from src.scoring import apply_vc_scorecard
from src.verification import is_source_supported

NOTES = "Company: Acme. Product automates invoice matching for mid-market finance teams."


def _category(record: DealRecord, name: str) -> int:
    return next(item.score for item in record.diligence_scorecard if name in item.category)


def test_signals_absent_from_notes_earn_no_credit():
    baseline = apply_vc_scorecard(DealRecord(description="Invoice matching software"), NOTES)
    invented = apply_vc_scorecard(
        DealRecord(
            description="Invoice matching software",
            traction_signals=["$2.4M ARR", "140% net revenue retention"],
            customer_signals=["Fortune 500 CFOs"],
            risks=["Competition from incumbents"],
        ),
        NOTES,
    )
    assert invented.opportunity_score == baseline.opportunity_score
    assert _category(invented, "Traction") == 0
    assert _category(invented, "Customer") == 0
    assert _category(invented, "Risk") == 0
    assert set(invented.unsupported_signals) == {
        "$2.4M ARR",
        "140% net revenue retention",
        "Fortune 500 CFOs",
        "Competition from incumbents",
    }


def test_signals_present_in_notes_still_earn_credit():
    notes = NOTES + " The company has $2.4M ARR and 140% net revenue retention."
    record = apply_vc_scorecard(
        DealRecord(traction_signals=["$2.4M ARR", "140% net revenue retention"]), notes
    )
    assert _category(record, "Traction") >= 12
    assert record.unsupported_signals == []


def test_changed_figure_is_not_supported():
    assert not is_source_supported("$3M ARR", "The company reports $2.4M ARR.")
    assert not is_source_supported("96% retention", "Gross retention was 69%.")


def test_equivalent_figure_formats_are_supported():
    assert is_source_supported("$420K ARR", "ARR reached $420,000 this year.")
    assert is_source_supported("$1.2M ARR", "ARR is $1,200,000.")
    assert is_source_supported("38% ARR growth", "ARR grew 38% over twelve months.")


def test_matching_figure_alone_is_not_enough():
    # The figure must appear alongside at least one word of the claim.
    assert not is_source_supported("96% retention", "96% of clinics are outpatient.")


def test_paraphrased_signal_needs_most_of_its_words_in_notes():
    notes = "Customers are clinic administrators and revenue-cycle teams."
    assert is_source_supported("Clinic administrators", notes)
    assert is_source_supported("Revenue-cycle teams", notes)
    assert not is_source_supported("Enterprise customers", notes)
    assert not is_source_supported("Hospital procurement teams", notes)
