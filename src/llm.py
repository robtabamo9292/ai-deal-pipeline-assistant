import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard, fallback_deal_record


load_dotenv()


def _extract_json(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

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

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        return fallback_deal_record(raw_notes)

    client = OpenAI(api_key=api_key)

    system_prompt = """
You are a private markets and venture diligence analyst.

Your job is to convert messy company notes into a structured CRM-ready deal record.

Important rules:
- Use only the information provided in the notes.
- Do not invent facts.
- If information is missing, use "Unknown".
- Be specific and concise.
- Diligence questions must be written as complete questions ending in question marks.
- Customer signals should describe customer segments, buyer personas, or user groups.
- Traction signals should describe evidence of demand, usage, growth, revenue, partnerships, or adoption.
- Funding signals should describe funding, valuation, investors, or financing context.
- Risks should be specific and useful for investor diligence.
- Recommended next step should be action-oriented and specific.
- The field "relationship_context" should be treated as "source context."
- Do not say "founder call" unless the provided source type explicitly says "Founder call notes."
- If source type is Research notes, Company website text, Funding announcement, Investor update, or Other, describe the source context accordingly.
- Return valid JSON only.
"""

    user_prompt = f"""
Analyze the company notes below and return a JSON object with exactly these fields:

{{
  "company_name": "string",
  "sector": "string",
  "subsector": "string",
  "business_model": "string",
  "stage": "string",
  "description": "string",
  "traction_signals": ["string"],
  "customer_signals": ["string"],
  "funding_signals": ["string"],
  "risks": ["string"],
  "diligence_questions": ["string"],
  "crm_tags": ["string"],
  "relationship_context": "string",
  "recommended_next_step": "string",
  "prompt_version": "v1.1-diligence-scorecard"
}}

Company notes:
{raw_notes}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1400,
    )

    content = response.choices[0].message.content
    data = _extract_json(content)

    data["traction_signals"] = _safe_list(data.get("traction_signals"))
    data["customer_signals"] = _safe_list(data.get("customer_signals"))
    data["funding_signals"] = _safe_list(data.get("funding_signals"))
    data["risks"] = _safe_list(data.get("risks"))
    data["diligence_questions"] = _safe_list(data.get("diligence_questions"))
    data["crm_tags"] = _safe_list(data.get("crm_tags"))

    data.setdefault("company_name", "Unknown")
    data.setdefault("sector", "Unknown")
    data.setdefault("subsector", "Unknown")
    data.setdefault("business_model", "Unknown")
    data.setdefault("stage", "Unknown")
    data.setdefault("description", "Unknown")
    data.setdefault("relationship_context", "Source context unavailable.")
    data.setdefault("recommended_next_step", "Unknown")
    data.setdefault("opportunity_score", 0)
    data.setdefault("confidence_score", 0)
    data.setdefault("priority", "Unknown")
    data.setdefault("prompt_version", "v1.1-diligence-scorecard")

    deal = DealRecord(**data)

    return apply_vc_scorecard(deal, raw_notes)