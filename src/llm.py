import json
import os
import re

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, fallback_deal_record

load_dotenv()


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    raise ValueError("Model response did not contain valid JSON.")


def _safe_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return []


def analyze_deal_with_llm(raw_notes: str) -> DealRecord:
    load_dotenv()
    normalized_notes = (raw_notes or "").strip()
    if not normalized_notes:
        raise ValueError("Deal notes cannot be empty.")

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        fallback = fallback_deal_record(normalized_notes)
        fallback.analysis_warning = (
            "No OPENAI_API_KEY was configured; AI analysis did not run."
        )
        return fallback
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")

    client = OpenAI(api_key=api_key)
    system_prompt = """
You are a private-markets diligence analyst. Convert source notes into a
structured CRM-ready deal record. Use only provided information, never invent
facts, and use Unknown when evidence is missing. Return valid JSON only.
The downstream score measures evidence completeness, not investment quality.
""".strip()
    user_prompt = f"""
Return a JSON object with exactly these fields:
company_name, sector, subsector, business_model, stage, description,
traction_signals, customer_signals, funding_signals, risks,
diligence_questions, crm_tags, relationship_context, recommended_next_step.

Company notes:
{normalized_notes}
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1400,
    )
    data = _extract_json(response.choices[0].message.content)
    for field in [
        "traction_signals",
        "customer_signals",
        "funding_signals",
        "risks",
        "diligence_questions",
        "crm_tags",
    ]:
        data[field] = _safe_list(data.get(field))
    for field in [
        "company_name",
        "sector",
        "subsector",
        "business_model",
        "stage",
        "description",
    ]:
        data.setdefault(field, "Unknown")
    data.setdefault("relationship_context", "Source context unavailable.")
    data.setdefault("recommended_next_step", "Unknown")
    data.update(
        {
            "analysis_path": "openai_chat_completions",
            "fallback_used": False,
            "analysis_warning": "",
            "model_name": model,
            "prompt_version": "v2.0-evidence-scorecard",
            "score_methodology": "evidence-completeness-v2",
        }
    )
    return apply_vc_scorecard(DealRecord(**data), normalized_notes)
