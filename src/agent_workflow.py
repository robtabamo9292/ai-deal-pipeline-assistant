import os
from typing import Any

from dotenv import load_dotenv

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, fallback_deal_record

load_dotenv()

try:
    from agents import Agent, Runner, function_tool
except ImportError:
    Agent = Runner = None

    def function_tool(func):
        func.name = func.__name__
        return func


@function_tool
def assess_note_quality(raw_notes: str) -> str:
    text = (raw_notes or "").strip().lower()
    if not text:
        return "The notes are empty."
    areas = {
        "company": ["product", "platform", "service", "software"],
        "customer": ["customer", "buyer", "user"],
        "traction": ["revenue", "growth", "retention", "usage"],
        "economics": ["pricing", "margin", "cac", "payback"],
        "risk": ["risk", "competition", "regulatory", "security"],
    }
    missing = [
        name
        for name, terms in areas.items()
        if not any(term in text for term in terms)
    ]
    if missing:
        return "Missing or weak evidence: " + ", ".join(missing)
    return "Core evidence areas are represented."


MODEL = (
    os.getenv("OPENAI_AGENT_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "gpt-4o-mini"
)

if Agent is not None:
    dealflow_agent = Agent(
        name="DealFlow Analyst Agent",
        model=MODEL,
        instructions="""
Convert the submitted notes into a DealRecord. Call assess_note_quality once.
Use only supplied information, use Unknown for gaps, and never invent facts.
The downstream score measures evidence completeness rather than investment quality.
""".strip(),
        tools=[assess_note_quality],
        output_type=DealRecord,
    )
else:
    class _UnavailableAgent:
        tools = [assess_note_quality]

    dealflow_agent = _UnavailableAgent()


def _coerce_deal_record(value: Any) -> DealRecord:
    if isinstance(value, DealRecord):
        return value
    if isinstance(value, dict):
        return DealRecord(**value)
    raise TypeError(
        f"Agents SDK returned unexpected output type: {type(value).__name__}"
    )


def analyze_deal_with_agents(raw_notes: str) -> DealRecord:
    normalized_notes = (raw_notes or "").strip()
    if not normalized_notes:
        raise ValueError("Deal notes cannot be empty.")
    if Runner is None:
        raise RuntimeError("OpenAI Agents SDK is not installed.")
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        fallback = fallback_deal_record(normalized_notes)
        fallback.analysis_warning = (
            "No OPENAI_API_KEY was configured; AI analysis did not run."
        )
        return fallback

    try:
        result = Runner.run_sync(dealflow_agent, normalized_notes)
        deal = _coerce_deal_record(result.final_output)
        deal.analysis_path = "agents_sdk"
        deal.fallback_used = False
        deal.model_name = MODEL
        return apply_vc_scorecard(deal, normalized_notes)
    except Exception as exc:
        raise RuntimeError(f"Agents SDK analysis failed: {exc}") from exc
