import pandas as pd


def _join_list(value):
    if not value:
        return ""

    return "; ".join(str(item) for item in value)


def _scorecard_summary(scorecard):
    if not scorecard:
        return ""

    return "; ".join(
        f"{item.category}: {item.score}/{item.max_score} ({item.evidence_level})"
        for item in scorecard
    )


def create_pipeline_dataframe(deals):
    rows = []

    for deal in deals:
        row = {
            "company_name": deal.company_name,
            "sector": deal.sector,
            "subsector": deal.subsector,
            "business_model": deal.business_model,
            "stage": deal.stage,
            "description": deal.description,
            "opportunity_score": deal.opportunity_score,
            "priority": deal.priority,
            "confidence_score": deal.confidence_score,
            "source_context": deal.relationship_context,
            "recommended_next_step": deal.recommended_next_step,
            "traction_signals": _join_list(deal.traction_signals),
            "customer_segments": _join_list(deal.customer_signals),
            "funding_signals": _join_list(deal.funding_signals),
            "risks": _join_list(deal.risks),
            "diligence_questions": _join_list(deal.diligence_questions),
            "crm_tags": _join_list(deal.crm_tags),
            "due_diligence_scorecard": _scorecard_summary(deal.diligence_scorecard),
            "prompt_version": deal.prompt_version,
        }

        for item in deal.diligence_scorecard:
            column_name = (
                item.category.lower()
                .replace(" / ", "_")
                .replace(" ", "_")
                .replace("-", "_")
            )
            row[f"{column_name}_score"] = f"{item.score}/{item.max_score}"
            row[f"{column_name}_evidence"] = item.evidence_level

        rows.append(row)

    return pd.DataFrame(rows)