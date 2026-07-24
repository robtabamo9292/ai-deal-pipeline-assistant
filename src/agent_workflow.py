import os
from typing import Any

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, fallback_deal_record


load_dotenv()


@function_tool
def assess_note_quality(raw_notes: str) -> str:
    """
    Review whether the submitted deal notes contain enough information
    for a useful private-markets diligence intake.

    Args:
        raw_notes: The complete company and diligence notes submitted
            for analysis.

    Returns:
        A concise assessment of the information that is present and
        the areas that require additional diligence.
    """
    text = (raw_notes or "").strip().lower()

    if not text:
        return (
            "The notes are empty. Mark unsupported fields as Unknown "
            "and request complete company information."
        )

    checks = {
        "company or product description": any(
            phrase in text
            for phrase in [
                "builds",
                "platform",
                "product",
                "solution",
                "provides",
                "offers",
                "develops",
                "software",
                "service",
            ]
        ),
        "customer or user context": any(
            phrase in text
            for phrase in [
                "customer",
                "buyer",
                "user",
                "enterprise",
                "smb",
                "consumer",
                "client",
                "business",
            ]
        ),
        "traction or adoption context": any(
            phrase in text
            for phrase in [
                "revenue",
                "arr",
                "growth",
                "users",
                "customers",
                "contracts",
                "retention",
                "usage",
                "adoption",
                "pipeline",
            ]
        ),
        "funding or valuation context": any(
            phrase in text
            for phrase in [
                "raising",
                "funding",
                "round",
                "valuation",
                "investor",
                "seed",
                "series",
                "capital",
                "financing",
            ]
        ),
        "risk or competition context": any(
            phrase in text
            for phrase in [
                "risk",
                "competition",
                "competitor",
                "regulatory",
                "compliance",
                "churn",
                "concentration",
                "privacy",
                "security",
            ]
        ),
    }

    missing_areas = [
        area
        for area, is_present in checks.items()
        if not is_present
    ]

    if not missing_areas:
        return (
            "The notes contain company, customer, traction, funding, "
            "and risk context and appear sufficient for an initial "
            "structured diligence intake."
        )

    return (
        "The notes are usable but missing or weak in these areas: "
        + ", ".join(missing_areas)
        + ". Mark unsupported facts as Unknown and generate specific "
        "follow-up diligence questions for these gaps."
    )


MODEL = (
    os.getenv("OPENAI_AGENT_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "gpt-4o-mini"
)


dealflow_agent = Agent(
    name="DealFlow Analyst Agent",
    model=MODEL,
    instructions="""
You are a private-markets and venture diligence analyst.

Convert unstructured company, founder, market, funding, traction,
customer, and source notes into a structured CRM-ready DealRecord.

Required process:
- Call assess_note_quality exactly once before finalizing the DealRecord.
- Use the tool output to identify information gaps and shape the
  diligence questions.
- Return a valid DealRecord object after the tool call.

Core rules:
- Use only information contained in the submitted notes.
- Do not invent facts, metrics, customers, funding, or market claims.
- If information is missing, use "Unknown".
- Clearly separate supplied facts from reasonable diligence assumptions.
- Be concise, practical, and investor-oriented.
- This output is not investment advice.

Extraction guidance:
- Customer signals should identify supported customer segments, buyer
  personas, or user groups.
- Infer customer segments only when they are explicit or strongly
  supported by the notes.
- Preserve source descriptions such as "Public source context,"
  "Founder call notes," "Pitch deck," "CRM notes," or "Website notes."
- Include traction metrics only when they appear in the submitted notes.
- Identify the business model only when supported by the notes, such as
  SaaS, transaction fees, marketplace take rate, services, licensing,
  or usage-based pricing.
- Do not treat funding as operating traction.

Investment-thesis guidance:
- The description field should function as a concise investment thesis.
- Explain what the company does.
- Explain why the opportunity could be attractive.
- Identify what must be true for the opportunity to succeed.
- Identify the most important diligence concerns.
- Keep the description under 350 words.

Risk guidance:
- Produce four to seven specific investment risks.
- Do not use "Unknown" as a risk.
- Avoid generic labels such as "Competition" or "Revenue quality"
  without explaining why the issue matters.
- Tie risks to the company, sector, business model, customer profile,
  valuation, regulation, data quality, or missing metrics.
- Inferred risks must be framed as diligence concerns rather than facts.

Diligence-question guidance:
- Each question must investigate a specific risk, information gap, or
  underwriting assumption.
- Each question must be complete and end with a question mark.
- Prioritize revenue quality, retention, customer concentration, unit
  economics, market size, differentiation, regulatory exposure, and
  go-to-market efficiency.

Recommended-next-step guidance:
- Make the next step specific and action-oriented.
- Tie it to the most important missing evidence.
- Example: "Request ARR, customer cohort, pricing, and retention data
  before advancing to the next diligence stage."

CRM guidance:
- CRM tags should be short, relevant, and useful for filtering a deal
  pipeline.

Return a valid DealRecord object.
""",
    tools=[assess_note_quality],
    output_type=DealRecord,
)


def _coerce_deal_record(value: Any) -> DealRecord:
    """
    Convert the Agents SDK result into a validated DealRecord.

    The configured output_type should normally return a DealRecord
    directly. Dictionary handling is retained as a defensive fallback.
    """
    if isinstance(value, DealRecord):
        return value

    if isinstance(value, dict):
        return DealRecord(**value)

    raise TypeError(
        "Agents SDK returned an unexpected output type: "
        f"{type(value).__name__}"
    )


def analyze_deal_with_agents(raw_notes: str) -> DealRecord:
    """
    Analyze raw deal notes using the OpenAI Agents SDK and then apply
    the deterministic diligence scorecard.

    When no API key is configured, the function returns the existing
    deterministic fallback record. Agents SDK runtime failures are
    raised to the calling application, which can decide whether to
    display an error or use another analysis path.
    """
    load_dotenv()

    normalized_notes = (raw_notes or "").strip()

    if not normalized_notes:
        raise ValueError("Deal notes cannot be empty.")

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if not api_key:
        fallback = fallback_deal_record(normalized_notes)
        fallback.risks.append(
            "No OPENAI_API_KEY was found, so deterministic fallback "
            "logic was used instead of Agents SDK analysis."
        )
        return fallback

    prompt = f"""
Analyze the following deal notes and produce a structured DealRecord.

Required process:
1. Call assess_note_quality using the complete deal notes below.
2. Review the tool's assessment of missing information.
3. Produce the final DealRecord using only the supplied notes.
4. Turn missing information into targeted diligence questions rather
   than invented facts.

Important output requirements:
- The description must be a high-level investment thesis rather than
  only a company summary.
- Explain what the company does, why it may be attractive, what must
  be true for the thesis to work, and the main diligence concerns.
- Keep the description under 350 words.
- Include four to seven specific investment risks.
- Do not use "Unknown" as a risk.
- When risks are inferred, frame them as areas requiring validation.
- Diligence questions must investigate the largest uncertainties.
- The recommended_next_step must be specific, action-oriented, and
  tied to the next diligence step.
- CRM tags must be concise and useful for pipeline filtering.

Deal notes:
{normalized_notes}
""".strip()

    try:
        result = Runner.run_sync(
            dealflow_agent,
            prompt,
        )

        deal = _coerce_deal_record(result.final_output)

        return apply_vc_scorecard(
            deal,
            normalized_notes,
        )

    except Exception as exc:
        raise RuntimeError(
            f"Agents SDK analysis failed: {exc}"
        ) from exc