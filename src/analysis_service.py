import logging
import os
from dataclasses import dataclass

from src.llm import analyze_deal_with_llm
from src.schema import DealRecord

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    deal: DealRecord
    primary_error: str = ""


def analyze_deal(raw_notes: str) -> AnalysisResult:
    """Run the preferred analysis path and expose fallback provenance."""
    try:
        from src.agent_workflow import analyze_deal_with_agents

        deal = analyze_deal_with_agents(raw_notes)
        if not deal.fallback_used:
            deal.analysis_path = "agents_sdk"
            deal.model_name = os.getenv("OPENAI_AGENT_MODEL") or os.getenv(
                "OPENAI_MODEL", "gpt-4o-mini"
            )
        return AnalysisResult(deal=deal)
    except Exception as exc:
        logger.warning(
            "Agents SDK analysis failed; using standard OpenAI path",
            exc_info=exc,
        )
        primary_error = f"{type(exc).__name__}: {exc}"

    try:
        deal = analyze_deal_with_llm(raw_notes)
        if not deal.fallback_used:
            deal.analysis_path = "openai_chat_completions"
            deal.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            deal.analysis_warning = (
                "The preferred Agents SDK path was unavailable; "
                "the standard OpenAI path was used."
            )
        return AnalysisResult(deal=deal, primary_error=primary_error)
    except Exception as exc:
        logger.exception("All AI analysis paths failed")
        raise RuntimeError(
            "Deal analysis failed in both the Agents SDK and standard OpenAI paths."
        ) from exc
