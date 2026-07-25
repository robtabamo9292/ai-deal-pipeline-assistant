from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.analysis_service import analyze_deal
from src.export import create_pipeline_dataframe
from src.llm import _extract_json, analyze_deal_with_llm
from src.memo import generate_investment_memo
from src.memo_pdf_v2 import memo_to_pdf_bytes
from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, determine_priority, fallback_deal_record


def make_deal() -> DealRecord:
    return DealRecord(
        company_name="Northstar Health",
        sector="Healthcare Software",
        subsector="Prior Authorization",
        business_model="Annual SaaS subscription",
        stage="Seed",
        description="Workflow software for specialty clinics.",
        traction_signals=[
            "$420K ARR",
            "12 paying clinics",
            "96% gross retention",
        ],
        customer_signals=[
            "Clinic administrators",
            "Revenue-cycle teams",
        ],
        funding_signals=["Seed stage"],
        risks=[
            "HIPAA compliance",
            "EHR integration complexity",
            "Small customer base",
        ],
        diligence_questions=["What is CAC payback?"],
        relationship_context="Fictional sample",
        recommended_next_step="Review cohorts and customer references.",
    )


def rich_notes() -> str:
    return """
Company: Northstar Health
Founder has 10 years of domain experience. Product automates prior authorization.
Customers are clinic administrators and revenue-cycle teams. 12 paying clinics,
$420K ARR, 96% retention, and 38% growth. Annual SaaS pricing, 78% gross margin,
14-month CAC payback. Founder-led outbound and billing partners. Competitors include
EHR modules. Risks include HIPAA, security, integration complexity, and concentration.
"""


def test_score_is_zero_for_no_supported_evidence():
    deal = DealRecord()
    scored = apply_vc_scorecard(deal, "")
    assert scored.opportunity_score == 0
    assert scored.priority == "Insufficient Evidence"


def test_negative_traction_counts_as_evidence_not_quality():
    deal = DealRecord(
        company_name="DeclineCo",
        sector="SaaS",
        business_model="Subscription",
        traction_signals=[
            "ARR declined 20%",
            "Retention fell to 70%",
        ],
        customer_signals=["Enterprise finance teams"],
        risks=["Churn increased"],
    )
    scored = apply_vc_scorecard(
        deal,
        "ARR declined 20%. Retention fell to 70%. Churn increased.",
    )
    assert scored.opportunity_score > 0
    assert scored.priority != "Diligence Ready"


@pytest.mark.parametrize(
    ("score", "confidence", "expected"),
    [
        (70, 65, "Diligence Ready"),
        (70, 64, "Review Evidence Gaps"),
        (50, 50, "Review Evidence Gaps"),
        (25, 50, "Early / Incomplete"),
        (24, 100, "Insufficient Evidence"),
    ],
)
def test_diligence_status_thresholds(score, confidence, expected):
    assert determine_priority(score, confidence) == expected


def test_score_bounds_are_enforced():
    with pytest.raises(ValidationError):
        DealRecord(opportunity_score=101)
    with pytest.raises(ValidationError):
        DealRecord(confidence_score=-1)


def test_extract_json_handles_wrapped_json_and_rejects_invalid():
    assert _extract_json('Result: {"company_name": "Acme"}') == {
        "company_name": "Acme"
    }
    with pytest.raises(ValueError):
        _extract_json("not json")


def test_missing_api_key_returns_visible_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    notes = (
        "Company: Acme\n"
        "The company builds workflow software for clinics."
    ) * 3
    deal = analyze_deal_with_llm(notes)
    assert deal.fallback_used is True
    assert deal.analysis_path == "deterministic_fallback"
    assert "OPENAI_API_KEY" in deal.analysis_warning


def test_analysis_service_preserves_deterministic_fallback_provenance(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    notes = "Company: Acme\nThe company builds workflow software for clinics."
    fallback = fallback_deal_record(notes)

    with patch(
        "src.agent_workflow.analyze_deal_with_agents",
        return_value=fallback,
    ):
        result = analyze_deal(notes)

    assert result.deal.fallback_used is True
    assert result.deal.analysis_path == "deterministic_fallback"
    assert result.deal.model_name == "none"


def test_mocked_llm_path(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        '{"company_name":"Acme","sector":"SaaS",'
                        '"subsector":"Workflow","business_model":"Subscription",'
                        '"stage":"Seed","description":"Workflow software",'
                        '"traction_signals":["$500K ARR"],'
                        '"customer_signals":["Clinics"],'
                        '"funding_signals":[],"risks":["Competition"],'
                        '"diligence_questions":["What is retention?"],'
                        '"crm_tags":["SaaS"],'
                        '"relationship_context":"Research notes",'
                        '"recommended_next_step":"Review cohorts"}'
                    )
                )
            )
        ]
    )
    client = MagicMock()
    client.chat.completions.create.return_value = response
    with patch("src.llm.OpenAI", return_value=client):
        notes = (
            "Company: Acme. $500K ARR. Clinics use the product. "
            "Subscription pricing."
        ) * 3
        deal = analyze_deal_with_llm(notes)
    assert deal.company_name == "Acme"
    assert deal.analysis_path == "openai_chat_completions"
    assert deal.fallback_used is False


def test_analysis_service_surfaces_primary_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with patch(
        "src.agent_workflow.analyze_deal_with_agents",
        side_effect=RuntimeError("agents unavailable"),
    ):
        with patch(
            "src.analysis_service.analyze_deal_with_llm",
            return_value=apply_vc_scorecard(make_deal(), rich_notes()),
        ):
            result = analyze_deal(rich_notes())
    assert "agents unavailable" in result.primary_error
    assert result.deal.analysis_path == "openai_chat_completions"
    assert result.deal.analysis_warning


def test_export_includes_provenance_and_evidence_names():
    deal = apply_vc_scorecard(make_deal(), rich_notes())
    dataframe = create_pipeline_dataframe([deal])
    expected = {
        "evidence_completeness_score",
        "diligence_status",
        "extraction_confidence",
        "analysis_path",
        "score_methodology",
        "prompt_version",
    }
    assert expected.issubset(dataframe.columns)


def test_pdf_contains_valid_bytes():
    deal = apply_vc_scorecard(make_deal(), rich_notes())
    memo = generate_investment_memo(deal)
    pdf = memo_to_pdf_bytes(memo)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1_000


def test_fallback_record_is_explicit():
    deal = fallback_deal_record(
        "Company: Acme Robotics\nBuilds robotics software."
    )
    assert deal.company_name == "Acme Robotics"
    assert deal.fallback_used is True
    assert deal.analysis_warning
    assert "Needs Review" in deal.crm_tags
