from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class DiligenceScorecardItem(BaseModel):
    category: str = Field(default="Unknown")
    score: int = Field(default=0, ge=0)
    max_score: int = Field(default=10, ge=1)
    evidence_level: str = Field(default="Insufficient")
    rationale: str = Field(default="Unknown")
    diligence_question: str = Field(default="Unknown")


class DealRecord(BaseModel):
    company_name: str = Field(default="Unknown")
    sector: str = Field(default="Unknown")
    subsector: str = Field(default="Unknown")
    business_model: str = Field(default="Unknown")
    stage: str = Field(default="Unknown")
    description: str = Field(default="Unknown")

    traction_signals: List[str] = Field(default_factory=list)
    customer_signals: List[str] = Field(default_factory=list)
    funding_signals: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    diligence_questions: List[str] = Field(default_factory=list)
    crm_tags: List[str] = Field(default_factory=list)

    relationship_context: str = Field(default="Unknown")
    recommended_next_step: str = Field(default="Unknown")

    # Retained for export compatibility. In v2 this is an evidence-completeness
    # score, not a prediction of investment quality or returns.
    opportunity_score: int = Field(default=0, ge=0, le=100)
    confidence_score: int = Field(default=0, ge=0, le=100)
    priority: str = Field(default="Unknown")

    diligence_scorecard: List[DiligenceScorecardItem] = Field(default_factory=list)

    prompt_version: str = Field(default="v2.0-evidence-scorecard")
    score_methodology: str = Field(default="evidence-completeness-v2")
    analysis_path: str = Field(default="unknown")
    fallback_used: bool = Field(default=False)
    analysis_warning: str = Field(default="")
    model_name: str = Field(default="unknown")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
