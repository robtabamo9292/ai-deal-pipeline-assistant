"""Auditable, explicitly curated offline demo for public portfolio review.

These are manually prepared fields from a FICTIONAL case; no model was run.
"""
from src.schema import DealRecord, EvidenceExcerpt
from src.scoring import apply_vc_scorecard


def curated_northstar_example(notes: str) -> DealRecord:
    deal = DealRecord(
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
    return apply_vc_scorecard(deal, notes)
