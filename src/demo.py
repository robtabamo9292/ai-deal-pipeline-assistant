"""Auditable, explicitly curated offline demo for public portfolio review.

These are manually prepared fields from a FICTIONAL case; no model was run.
"""
from src.schema import DealRecord, EvidenceExcerpt
from src.scoring import apply_vc_scorecard


def _northstar_record() -> DealRecord:
    """The curated fictional extraction, before scoring."""
    return DealRecord(
        company_name="Northstar Health",
        sector="Healthcare Software",
        subsector="Prior-authorization workflow",
        stage="Seed",
        description="Workflow software automating prior-authorization intake for specialty clinics.",
        business_model="Annual SaaS contracts per clinic and authorization volume",
        traction_signals=[
            "12 paying clinics",
            "$420,000 ARR and 38% growth over twelve months",
            "96% gross retention and three paid pilots",
        ],
        customer_signals=[
            "Clinic administrators at specialty practices",
            "Revenue-cycle teams at specialty practices",
        ],
        risks=[
            "HIPAA compliance",
            "EHR integration complexity",
            "Small customer base and unproven acquisition efficiency",
        ],
        evidence_excerpts=[
            EvidenceExcerpt(
                category="Traction", claim="12 paying clinics and $420,000 ARR",
                quote="12 paying clinics, $420,000 ARR",
            ),
            EvidenceExcerpt(
                category="Business model", claim="Annual SaaS pricing per location and volume",
                quote="Annual SaaS contracts priced by clinic location and authorization volume",
            ),
            EvidenceExcerpt(
                category="Risk", claim="HIPAA and integration risks disclosed",
                quote="HIPAA compliance, EHR integration complexity",
            ),
        ],
        relationship_context="Fictional, manually curated demonstration.",
        recommended_next_step="Review customer cohorts and security controls.",
        analysis_path="curated_offline_demo",
        analysis_warning=(
            "Fictional sample with manually prepared structured fields. "
            "No AI extraction or external verification was performed."
        ),
        model_name="none",
        prompt_version="not-run",
    )


def curated_northstar_example(notes: str) -> DealRecord:
    return apply_vc_scorecard(_northstar_record(), notes)


# Claims a model could plausibly invent: none of them appear in the notes.
PLANTED_TRACTION = ["$1.2M ARR", "140% net revenue retention"]
PLANTED_CUSTOMERS = ["Fortune 500 health systems"]
PLANTED_QUOTE = "ARR reached $1.2M last quarter"


def curated_planted_claims_example(notes: str) -> DealRecord:
    """The curated Northstar extraction plus claims the notes do not support.

    Demonstrates the source check without an API key: the planted claims are
    flagged as unsupported, the invented quote is not found, and the score
    matches the clean extraction because the planted claims earn nothing.
    """
    deal = _northstar_record()
    deal.company_name = "Northstar Health (planted claims)"
    deal.traction_signals += PLANTED_TRACTION
    deal.customer_signals += PLANTED_CUSTOMERS
    deal.evidence_excerpts += [
        EvidenceExcerpt(category="Traction", claim="ARR of $1.2M", quote=PLANTED_QUOTE)
    ]
    deal.analysis_path = "curated_offline_demo_planted_claims"
    deal.analysis_warning = (
        "Fictional sample: the curated Northstar extraction with three planted "
        "claims that are not in the notes ($1.2M ARR, 140% net revenue "
        "retention, Fortune 500 health systems) and one invented quote. "
        "No AI extraction was performed."
    )
    return apply_vc_scorecard(deal, notes)
