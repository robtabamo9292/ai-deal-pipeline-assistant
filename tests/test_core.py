import pytest
from pydantic import ValidationError

from src.agent_workflow import dealflow_agent
from src.export import create_pipeline_dataframe
from src.memo import generate_investment_memo
from src.memo_pdf import memo_to_pdf_bytes
from src.schema import DealRecord
from src.scoring import determine_priority, fallback_deal_record


def make_sample_deal() -> DealRecord:
    return DealRecord(
        company_name="Acme Robotics",
        sector="Artificial Intelligence",
        subsector="Robotics",
        business_model="Enterprise SaaS",
        stage="Seed",
        description="AI software for automating industrial robotics workflows.",
        traction_signals=["$500K ARR", "Three enterprise customers"],
        customer_signals=["Manufacturing companies"],
        funding_signals=["Raised a $2M seed round"],
        risks=["Long enterprise sales cycles"],
        diligence_questions=["What is customer retention?"],
        crm_tags=["AI", "Robotics"],
        relationship_context="Founder introduction",
        recommended_next_step="Schedule a diligence call.",
        opportunity_score=82,
        confidence_score=74,
        priority="Medium / High Priority",
    )


def test_agent_quality_tool_is_registered():
    tool_names = [
        getattr(tool, "name", type(tool).__name__)
        for tool in dealflow_agent.tools
    ]

    assert "assess_note_quality" in tool_names


@pytest.mark.parametrize(
    ("opportunity_score", "confidence_score", "expected"),
    [
        (85, 70, "High Priority"),
        (85, 69, "Medium / High Priority"),
        (75, 50, "Medium / High Priority"),
        (60, 50, "Needs Diligence"),
        (40, 50, "Low Priority"),
        (39, 100, "Pass / Insufficient Info"),
    ],
)
def test_priority_thresholds(
    opportunity_score,
    confidence_score,
    expected,
):
    assert determine_priority(opportunity_score, confidence_score) == expected


def test_deal_score_bounds_are_enforced():
    with pytest.raises(ValidationError):
        DealRecord(opportunity_score=101)

    with pytest.raises(ValidationError):
        DealRecord(confidence_score=-1)


def test_memo_preserves_core_deal_information():
    deal = make_sample_deal()
    memo = generate_investment_memo(deal)

    assert memo.company_name == "Acme Robotics"
    assert memo.sector == "Artificial Intelligence"
    assert memo.opportunity_score == 82
    assert memo.confidence_score == 74
    assert "Acme Robotics" in memo.executive_summary


def test_pipeline_export_contains_expected_columns():
    deal = make_sample_deal()
    dataframe = create_pipeline_dataframe([deal])

    expected_columns = {
        "company_name",
        "sector",
        "stage",
        "opportunity_score",
        "confidence_score",
        "priority",
        "recommended_next_step",
        "prompt_version",
    }

    assert expected_columns.issubset(dataframe.columns)
    assert len(dataframe) == 1
    assert dataframe.loc[0, "company_name"] == "Acme Robotics"
    assert dataframe.loc[0, "opportunity_score"] == 82


def test_pdf_generation_returns_valid_pdf_bytes():
    deal = make_sample_deal()
    memo = generate_investment_memo(deal)
    pdf_bytes = memo_to_pdf_bytes(memo)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000


def test_fallback_record_extracts_company_and_stays_bounded():
    notes = """
Company: Acme Robotics
The company develops robotics software for manufacturers.
"""

    deal = fallback_deal_record(notes)

    assert deal.company_name == "Acme Robotics"
    assert 0 <= deal.opportunity_score <= 100
    assert 0 <= deal.confidence_score <= 100
    assert deal.diligence_scorecard
    assert "Needs Review" in deal.crm_tags
