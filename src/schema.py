from typing import List
from pydantic import BaseModel, Field


class DiligenceScorecardItem(BaseModel):
    category: str = Field(default="Unknown")
    score: int = Field(default=0, ge=0)
    max_score: int = Field(default=10, ge=1)
    evidence_level: str = Field(default="Unknown")
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

    opportunity_score: int = Field(default=0, ge=0, le=100)
    confidence_score: int = Field(default=0, ge=0, le=100)
    priority: str = Field(default="Unknown")

    diligence_scorecard: List[DiligenceScorecardItem] = Field(default_factory=list)

    prompt_version: str = Field(default="v1.1-vc-scorecard")