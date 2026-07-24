from src.memo_schema import InvestmentMemo
from src.schema import DealRecord


def _join(items):
    return "; ".join(str(item) for item in items or []) or "Not provided"


def generate_investment_memo(
    deal: DealRecord,
    raw_notes: str = "",
) -> InvestmentMemo:
    thesis = (
        [deal.description]
        if deal.description and deal.description != "Unknown"
        else []
    )
    if deal.traction_signals:
        thesis.append(
            f"Documented traction evidence includes: {_join(deal.traction_signals)}."
        )
    if deal.customer_signals:
        thesis.append(
            f"Documented customer evidence includes: {_join(deal.customer_signals)}."
        )
    if not thesis:
        thesis = [
            "The supplied notes do not yet support a complete investment thesis."
        ]

    executive_summary = (
        f"{deal.company_name} is presented as a {deal.stage} company in "
        f"{deal.sector}. The evidence-completeness score is "
        f"{deal.opportunity_score}/100 and the diligence status is "
        f"{deal.priority}. This score measures documented diligence coverage, "
        f"not investment quality. Recommended next step: "
        f"{deal.recommended_next_step}"
    )
    overview = (
        f"{deal.company_name} operates in {deal.sector}"
        f"{' / ' + deal.subsector if deal.subsector and deal.subsector != 'Unknown' else ''}. "
        f"Business model: {deal.business_model}. "
        f"Source context: {deal.relationship_context}."
    )
    return InvestmentMemo(
        company_name=deal.company_name,
        sector=deal.sector,
        subsector=deal.subsector,
        stage=deal.stage,
        opportunity_score=deal.opportunity_score,
        priority=deal.priority,
        confidence_score=deal.confidence_score,
        executive_summary=executive_summary,
        company_overview=overview,
        investment_thesis=thesis,
        traction_and_customers=(
            f"Traction: {_join(deal.traction_signals)}. "
            f"Customers: {_join(deal.customer_signals)}. "
            f"Funding: {_join(deal.funding_signals)}."
        ),
        key_risks=deal.risks or ["Risk evidence was not provided."],
        diligence_questions=deal.diligence_questions,
        recommended_next_steps=[deal.recommended_next_step],
        source_limitations=(
            "Uses only the supplied notes. No claims were independently "
            "verified. The evidence score measures completeness and is not "
            "an investment recommendation."
        ),
        score_methodology=deal.score_methodology,
        analysis_path=deal.analysis_path,
        model_name=deal.model_name,
        prompt_version=deal.prompt_version,
        generated_at=deal.generated_at,
    )
