import pandas as pd


def _join_list(value):
    return "; ".join(str(item) for item in value or [])


def _scorecard_summary(scorecard):
    return "; ".join(
        f"{item.category}: {item.score}/{item.max_score} ({item.evidence_level})"
        for item in scorecard or []
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
            "evidence_completeness_score": deal.opportunity_score,
            "diligence_status": deal.priority,
            "extraction_confidence": deal.confidence_score,
            "source_context": deal.relationship_context,
            "recommended_next_step": deal.recommended_next_step,
            "traction_signals": _join_list(deal.traction_signals),
            "customer_segments": _join_list(deal.customer_signals),
            "funding_signals": _join_list(deal.funding_signals),
            "risks": _join_list(deal.risks),
            "diligence_questions": _join_list(deal.diligence_questions),
            "crm_tags": _join_list(deal.crm_tags),
            "due_diligence_scorecard": _scorecard_summary(
                deal.diligence_scorecard
            ),
            "score_methodology": deal.score_methodology,
            "analysis_path": deal.analysis_path,
            "fallback_used": deal.fallback_used,
            "analysis_warning": deal.analysis_warning,
            "model_name": deal.model_name,
            "prompt_version": deal.prompt_version,
            "generated_at": deal.generated_at,
            # Backward-compatible aliases.
            "opportunity_score": deal.opportunity_score,
            "priority": deal.priority,
            "confidence_score": deal.confidence_score,
        }
        for item in deal.diligence_scorecard:
            column = (
                item.category.lower()
                .replace(" / ", "_")
                .replace(" ", "_")
                .replace("-", "_")
            )
            row[f"{column}_score"] = item.score
            row[f"{column}_max"] = item.max_score
            row[f"{column}_evidence"] = item.evidence_level
        rows.append(row)
    return pd.DataFrame(rows)
