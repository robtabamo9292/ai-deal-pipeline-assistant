from typing import List
from pydantic import BaseModel, Field


class InvestmentMemo(BaseModel):
    company_name: str = Field(default="Unknown")
    sector: str = Field(default="Unknown")
    subsector: str = Field(default="Unknown")
    stage: str = Field(default="Unknown")
    opportunity_score: int = Field(default=0)
    priority: str = Field(default="Unknown")
    confidence_score: int = Field(default=0)

    executive_summary: str = Field(default="Unknown")
    company_overview: str = Field(default="Unknown")
    investment_thesis: List[str] = Field(default_factory=list)
    market_opportunity: str = Field(default="Unknown")
    product_and_differentiation: str = Field(default="Unknown")
    traction_and_customers: str = Field(default="Unknown")
    business_model: str = Field(default="Unknown")
    go_to_market: str = Field(default="Unknown")
    key_risks: List[str] = Field(default_factory=list)
    diligence_questions: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    source_limitations: str = Field(
        default="Uses only the information provided by the user. Requires human review."
    )