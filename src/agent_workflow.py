import os
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, fallback_deal_record

load_dotenv()


@function_tool
def assess_note_quality(raw_notes: str) -> str:
    """
    Reviews whether the pasted deal notes contain enough information
    for a useful private-markets diligence intake.
    """
    text = (raw_notes or "").lower()

    checks = {
        "company_description": any(
            word in text for word in ["company", "builds", "platform", "product", "solution"]
        ),
        "customer_context": any(
            word in text for word in ["customer", "buyer", "user", "enterprise", "smb", "consumer"]
        ),
        "traction_context": any(
            word in text for word in ["revenue", "arr", "growth", "users", "customers", "contracts", "retention"]
        ),
        "funding_context": any(
            word in text for word in ["raising", "funding", "round", "valuation", "investor", "seed", "series"]
        ),
        "risk_context": any(
            word in text for word in ["risk", "competition", "regulatory", "compliance", "churn", "concentration"]
        ),
    }

    missing = [field for field, present in checks.items() if not present]

    if not missing:
        return "The notes appear strong enough for a structured diligence intake."

    return (
        "The notes are usable, but missing or weak in these areas: "
        + ", ".join(missing)
        + ". Mark missing facts as Unknown and generate follow-up diligence questions."
    )


MODEL = os.getenv("OPENAI_AGENT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

dealflow_agent = Agent(
    name="DealFlow Analyst Agent",
    model=MODEL,
    instructions="""
    You are a private markets and venture diligence analyst.

    Convert messy company, founder, market, funding, and research notes into
    a structured CRM-ready deal record.

    Rules:
    - Use only the information provided in the notes.
    - Do not invent facts.
    - If information is missing, use "Unknown".
    - Be concise, practical, and diligence-oriented.
    - Always call assess_note_quality before finalizing the record.
    - Risks should be specific and useful for investor diligence.
    - Diligence questions must be complete questions ending in question marks.
    - Recommended next step should be action-oriented.
    - This is not investment advice.

    Return a valid DealRecord object.
    """,
    tools=[assess_note_quality],
    output_type=DealRecord,
)


def analyze_deal_with_agents(raw_notes: str) -> DealRecord:
    """
    Analyze raw deal notes using the OpenAI Agents SDK, then apply
    the existing deterministic scorecard logic.
    """
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        return fallback_deal_record(raw_notes)

    prompt = f"""
    Analyze the following deal notes and produce a structured DealRecord.

    Deal notes:
    {raw_notes}
    """

    try:
        result = Runner.run_sync(dealflow_agent, prompt)
        deal = result.final_output

        if isinstance(deal, dict):
            deal = DealRecord(**deal)

        return apply_vc_scorecard(deal, raw_notes)

    except Exception as exc:
        fallback = fallback_deal_record(raw_notes)
        fallback.risks.append(f"Agents SDK analysis failed and fallback logic was used: {exc}")
        return fallback
