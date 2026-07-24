import re
from typing import Iterable, List

from src.schema import DealRecord, DiligenceScorecardItem


UNKNOWN_VALUES = {"", "unknown", "n/a", "none", "not provided"}


def _clean_text(value) -> str:
    return str(value or "").strip()


def _is_known(value) -> bool:
    return _clean_text(value).lower() not in UNKNOWN_VALUES


def _known_items(values: Iterable[object]) -> list[str]:
    return [str(value).strip() for value in values or [] if _is_known(value)]


def _has_any(text: str, phrases: Iterable[str]) -> bool:
    normalized = text.lower()
    return any(phrase.lower() in normalized for phrase in phrases)


def _has_quantitative_evidence(values: Iterable[str]) -> bool:
    return any(re.search(r"[$%\d]", value or "") for value in values or [])


def _score_parts(parts: list[tuple[bool, int]], max_score: int) -> int:
    """Sum explicit evidence points. Missing evidence receives zero points."""
    return max(0, min(max_score, sum(points for present, points in parts if present)))


def _evidence_level(score: int, max_score: int) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.75:
        return "Strong"
    if ratio >= 0.45:
        return "Partial"
    if score > 0:
        return "Limited"
    return "Insufficient"


def _item(category: str, score: int, max_score: int, rationale: str, question: str) -> DiligenceScorecardItem:
    return DiligenceScorecardItem(
        category=category,
        score=score,
        max_score=max_score,
        evidence_level=_evidence_level(score, max_score),
        rationale=rationale,
        diligence_question=question,
    )


def build_due_diligence_scorecard(deal: DealRecord, raw_notes: str) -> List[DiligenceScorecardItem]:
    """Measure evidence completeness, not investment attractiveness."""
    notes = _clean_text(raw_notes)
    traction = _known_items(deal.traction_signals)
    customers = _known_items(deal.customer_signals)
    risks = _known_items(deal.risks)

    team_score = _score_parts([
        (_has_any(notes, ["founder", "co-founder", "ceo", "management team"]), 6),
        (_has_any(notes, ["background", "experience", "domain expertise", "previously"]), 5),
        (_has_any(notes, ["track record", "prior exit", "repeat founder", "operator"]), 4),
    ], 15)
    market_score = _score_parts([
        (_is_known(deal.sector), 4),
        (len(customers) >= 1, 4),
        (_has_any(notes, ["market size", "tam", "addressable market", "budget"]), 4),
        (_has_any(notes, ["why now", "tailwind", "urgent", "regulatory driver"]), 3),
    ], 15)
    product_score = _score_parts([
        (_is_known(deal.description), 6),
        (_is_known(deal.subsector), 3),
        (_has_any(notes, ["workflow", "integration", "proprietary", "differentiation"]), 3),
        (_has_any(notes, ["switching cost", "network effect", "data advantage", "moat"]), 3),
    ], 15)
    traction_score = _score_parts([
        (len(traction) >= 1, 5),
        (len(traction) >= 2, 3),
        (_has_quantitative_evidence(traction), 4),
        (_has_any(notes, ["retention", "cohort", "renewal", "repeat usage"]), 3),
    ], 15)
    customer_score = _score_parts([
        (len(customers) >= 1, 4),
        (len(customers) >= 2, 2),
        (_has_any(notes, ["buyer", "economic buyer", "decision maker"]), 2),
        (_has_any(notes, ["use case", "pain point", "job to be done"]), 2),
    ], 10)
    business_model_score = _score_parts([
        (_is_known(deal.business_model), 4),
        (_has_any(notes, ["pricing", "subscription", "usage-based", "take rate"]), 2),
        (_has_any(notes, ["gross margin", "cac", "payback", "ltv"]), 2),
        (_has_any(notes, ["expansion", "upsell", "net retention", "renewal"]), 2),
    ], 10)
    gtm_score = _score_parts([
        (_has_any(notes, ["go-to-market", "gtm", "sales channel", "distribution"]), 3),
        (_has_any(notes, ["pipeline", "conversion", "sales cycle", "outbound", "inbound"]), 3),
        (_has_any(notes, ["partner", "self-serve", "product-led", "plg"]), 2),
    ], 8)
    competition_score = _score_parts([
        (_has_any(notes, ["competitor", "competition", "incumbent", "alternative"]), 3),
        (_has_any(notes, ["differentiation", "switching cost", "moat", "defensible"]), 2),
        (any(_has_any(risk, ["compet", "incumbent", "substitute"]) for risk in risks), 2),
    ], 7)
    risk_score = _score_parts([
        (len(risks) >= 1, 2),
        (len(risks) >= 3, 1),
        (_has_any(notes, ["regulatory", "privacy", "security", "compliance", "legal"]), 1),
        (_has_any(notes, ["concentration", "churn", "runway", "execution risk"]), 1),
    ], 5)

    configs = [
        ("Founder / Team Evidence", team_score, 15, "Measures concrete team and track-record evidence.", "What founder, team, and execution evidence is still missing?"),
        ("Market Evidence", market_score, 15, "Measures market definition, customer context, sizing, and timing evidence.", "What market size, budget ownership, and why-now evidence should be validated?"),
        ("Product / Differentiation Evidence", product_score, 15, "Measures product clarity and differentiation evidence.", "What product evidence shows a durable advantage over alternatives?"),
        ("Traction / PMF Evidence", traction_score, 15, "Measures the presence and specificity of traction and retention evidence.", "What quantitative traction, retention, and cohort evidence is missing?"),
        ("Customer / ICP Evidence", customer_score, 10, "Measures clarity on users, buyers, and customer segmentation.", "Who is the buyer, who is the user, and which use case has the strongest urgency?"),
        ("Business Model Evidence", business_model_score, 10, "Measures pricing, monetization, margin, and unit-economics evidence.", "What pricing, margin, CAC, payback, and retention evidence is missing?"),
        ("GTM Evidence", gtm_score, 8, "Measures whether acquisition channels and sales repeatability are documented.", "Which acquisition channels are repeatable beyond founder-led selling?"),
        ("Competitive Evidence", competition_score, 7, "Measures whether alternatives, competitors, and defensibility are documented.", "Which competitors and substitutes matter most, and why will the company win?"),
        ("Risk Evidence", risk_score, 5, "Measures whether material operating, legal, and concentration risks are identified.", "Which risks could invalidate the thesis, and what evidence would reduce them?"),
    ]
    return [_item(*config) for config in configs]


def generate_priority_diligence_questions(deal: DealRecord, scorecard: List[DiligenceScorecardItem], max_questions: int = 8) -> List[str]:
    questions: list[str] = []
    for question in deal.diligence_questions:
        normalized = _clean_text(question)
        if normalized and not normalized.endswith("?"):
            normalized += "?"
        if normalized and normalized not in questions:
            questions.append(normalized)
    for item in sorted(scorecard, key=lambda row: row.score / row.max_score):
        if item.diligence_question not in questions:
            questions.append(item.diligence_question)
        if len(questions) >= max_questions:
            break
    return questions[:max_questions]


def calculate_confidence_score(deal: DealRecord, raw_notes: str, scorecard: List[DiligenceScorecardItem]) -> int:
    """Estimate extraction confidence from completeness, not factual truth."""
    key_fields = [deal.company_name, deal.sector, deal.subsector, deal.business_model, deal.stage, deal.description, deal.recommended_next_step]
    field_score = round(sum(_is_known(value) for value in key_fields) / len(key_fields) * 40)
    signal_count = sum(len(_known_items(values)) for values in [deal.traction_signals, deal.customer_signals, deal.funding_signals, deal.risks, deal.diligence_questions])
    signal_score = min(30, signal_count * 3)
    notes_score = min(15, len(_clean_text(raw_notes)) // 200)
    evidence_score = round(sum(item.score / item.max_score for item in scorecard) / len(scorecard) * 15) if scorecard else 0
    return max(0, min(100, field_score + signal_score + notes_score + evidence_score))


def determine_priority(evidence_score: int, confidence_score: int) -> str:
    if evidence_score >= 70 and confidence_score >= 65:
        return "Diligence Ready"
    if evidence_score >= 50:
        return "Review Evidence Gaps"
    if evidence_score >= 25:
        return "Early / Incomplete"
    return "Insufficient Evidence"


def apply_vc_scorecard(deal: DealRecord, raw_notes: str) -> DealRecord:
    scorecard = build_due_diligence_scorecard(deal, raw_notes)
    deal.diligence_scorecard = scorecard
    deal.opportunity_score = max(0, min(100, sum(item.score for item in scorecard)))
    deal.confidence_score = calculate_confidence_score(deal, raw_notes, scorecard)
    deal.priority = determine_priority(deal.opportunity_score, deal.confidence_score)
    deal.diligence_questions = generate_priority_diligence_questions(deal, scorecard)
    deal.score_methodology = "evidence-completeness-v2"
    deal.prompt_version = "v2.0-evidence-scorecard"
    if not _is_known(deal.recommended_next_step):
        lowest = sorted(scorecard, key=lambda row: row.score / row.max_score)[:3]
        focus = ", ".join(item.category.lower() for item in lowest)
        deal.recommended_next_step = f"Collect additional evidence for {focus} before advancing."
    return deal


def _extract_company_name(raw_notes: str) -> str:
    for pattern in [r"Company:\s*(.+)", r"Company name:\s*(.+)", r"Startup:\s*(.+)"]:
        match = re.search(pattern, raw_notes, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Unknown Company"


def fallback_deal_record(raw_notes: str) -> DealRecord:
    deal = DealRecord(
        company_name=_extract_company_name(raw_notes),
        description="AI extraction was unavailable. Review the source notes manually.",
        risks=["Automated extraction was unavailable; manual review is required."],
        diligence_questions=["What does the company do?", "Who are the customers and buyers?", "What traction has the company achieved?", "What is the business model?", "What are the main risks?"],
        crm_tags=["Needs Review"],
        relationship_context="Source context unavailable.",
        recommended_next_step="Check API configuration or review the notes manually.",
        analysis_path="deterministic_fallback",
        fallback_used=True,
        analysis_warning="AI analysis was unavailable; deterministic fallback logic was used.",
        model_name="none",
    )
    return apply_vc_scorecard(deal, raw_notes)
