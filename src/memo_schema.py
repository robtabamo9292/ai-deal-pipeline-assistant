from typing import List

from pydantic import BaseModel, Field


class InvestmentMemo(BaseModel):
    company_name: str = "Unknown"
    sector: str = "Unknown"
    subsector: str = "Unknown"
    stage: str = "Unknown"
    opportunity_score: int = 0
    priority: str = "Unknown"
    confidence_score: int = 0
    executive_summary: str = "Unknown"
    company_overview: str = "Unknown"
    investment_thesis: List[str] = Field(default_factory=list)
    traction_and_customers: str = "Unknown"
    key_risks: List[str] = Field(default_factory=list)
    diligence_questions: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    source_limitations: str = (
        "Uses only supplied notes and requires human review."
    )
    score_methodology: str = "evidence-completeness-v2"
    analysis_path: str = "unknown"
    model_name: str = "unknown"
    prompt_version: str = "v2.0-evidence-scorecard"
    generated_at: str = "unknown"
