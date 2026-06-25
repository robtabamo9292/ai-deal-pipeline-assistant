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

    Convert messy company, founder, market, funding, traction, customer,
    and source notes into a structured CRM-ready deal record.

    Core rules:
    - Use only the information provided in the notes.
    - Do not invent facts.
    - If information is missing, use "Unknown".
    - Separate facts from assumptions.
    - Be concise, practical, and investor-oriented.
    - Always call assess_note_quality before finalizing the record.
    - This is not investment advice.

    Extraction guidance:
    - Customer Segments: infer only from explicit or strongly implied context.
      Example: if the company sells spend management software to businesses,
      use "Businesses, finance teams, and operators" rather than "Unknown".
    - Source Context: preserve phrases such as "Public source context",
      "Founder call notes", "Pitch deck", "CRM notes", or "Website notes" when present.
    - Traction: include numbers, customers, ARR/revenue, growth, usage, pilots,
      retention, or funding signals only when provided.
    - Business Model: identify likely model only if supported by notes, such as
      SaaS, transaction fees, marketplace take rate, services, or usage-based pricing.

    Risk guidance:
    - Avoid generic risks like "Revenue quality" or "Competition" by themselves.
    - Each risk should explain why it matters for diligence.
    - Prefer specific investor-style risks tied to the notes or missing data.

    Diligence question guidance:
    - Each question should map to a specific risk, missing field, or underwriting assumption.
    - Questions must be complete questions ending with a question mark.
    - Prioritize questions about revenue quality, retention, customer concentration,
      unit economics, market size, competitive differentiation, and GTM efficiency.

    Recommended next step:
    - Make the next step specific and action-oriented.
      Example: "Request ARR, customer cohort, pricing, and retention data before advancing."

    Return a valid DealRecord object.

    """,
    tools=[assess_note_quality],
    output_type=DealRecord,
)


def analyze_deal_with_agents(raw_notes: str) -> DealRecord:
    """
    Analyze raw deal notes using the OpenAI Agents SDK, then apply
    the existing deterministic scorecard logic.

    Fallback logic is used only when no API key is available. Runtime
    failures from the Agents SDK are raised so the UI can surface them
    instead of showing a successful analysis.
    """
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        fallback = fallback_deal_record(raw_notes)
        fallback.risks.append(
            "No OPENAI_API_KEY was found, so fallback logic was used instead of Agents SDK analysis."
        )
        return fallback

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
        raise RuntimeError(f"Agents SDK analysis failed: {exc}") from exc
