import re
from typing import List

from src.schema import DealRecord, DiligenceScorecardItem


def _clean_text(value) -> str:
    return str(value or "").strip()


def _is_known(value) -> bool:
    text = _clean_text(value).lower()
    return bool(text) and text not in {"unknown", "n/a", "none", "not provided"}


def _has_source_link(raw_notes: str) -> bool:
    text = _clean_text(raw_notes).lower()
    return "http://" in text or "https://" in text or "source:" in text or "citation:" in text


def _count_keyword_hits(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in text_lower)


def _evidence_level(score: int, max_score: int) -> str:
    ratio = score / max_score if max_score else 0

    if ratio >= 0.80:
        return "High"
    if ratio >= 0.55:
        return "Medium"
    if ratio >= 0.35:
        return "Low"
    return "Insufficient"


def _score_from_hits(hits: int, max_score: int, baseline_ratio: float = 0.30) -> int:
    if hits >= 4:
        ratio = 0.92
    elif hits == 3:
        ratio = 0.82
    elif hits == 2:
        ratio = 0.68
    elif hits == 1:
        ratio = 0.52
    else:
        ratio = baseline_ratio

    return max(0, min(max_score, round(max_score * ratio)))


def _normalize_question(question: str) -> str:
    question = _clean_text(question)

    if not question:
        return ""

    if question.endswith("?"):
        return question

    return f"What evidence supports {question.lower()}?"


def _extract_company_name(raw_notes: str) -> str:
    patterns = [
        r"Company:\s*(.+)",
        r"Company name:\s*(.+)",
        r"Startup:\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_notes, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return "Unknown Company"


def build_due_diligence_scorecard(deal: DealRecord, raw_notes: str) -> List[DiligenceScorecardItem]:
    notes = _clean_text(raw_notes)

    config = [
        {
            "category": "Founder / Team Fit",
            "max_score": 15,
            "keywords": [
                "founder", "co-founder", "ceo", "team", "operator", "domain expertise",
                "previously built", "background", "experience", "founder-market fit"
            ],
            "rationale_high": "Founder or team context appears meaningfully supported in the notes.",
            "rationale_low": "Founder-market fit and team background need more validation.",
            "question": "What evidence supports founder-market fit and execution credibility?"
        },
        {
            "category": "Market Opportunity",
            "max_score": 15,
            "keywords": [
                "tam", "sam", "som", "market", "large market", "addressable market",
                "demand", "budget", "category", "why now", "tailwind", "growth market",
                "urgent pain", "market opportunity", "platform opportunity", "enterprise demand",
                "consumer demand", "regulatory tailwind", "secular growth", "market size",
                "expanding market", "emerging demand", "willingness to pay"
            ],
            "rationale_high": "The notes suggest a sizable and timely market opportunity.",
            "rationale_low": "Market size, urgency, and budget ownership need more validation.",
            "question": "How large is the addressable market, and why is now the right time for this company?"
        },
        {
            "category": "Product / Differentiation",
            "max_score": 15,
            "keywords": [
                "product", "platform", "workflow", "ai", "automation", "proprietary",
                "differentiated", "data", "model", "technology", "unique", "wedge",
                "infrastructure", "integrated", "native", "full-stack"
            ],
            "rationale_high": "The product wedge and differentiation are reasonably clear.",
            "rationale_low": "The product wedge and defensibility need more detail.",
            "question": "What does the product do that incumbents or substitutes cannot easily replicate?"
        },
        {
            "category": "Traction / PMF Evidence",
            "max_score": 15,
            "keywords": [
                "revenue", "arr", "growth", "users", "customers", "retention", "usage",
                "contracts", "pipeline", "adoption", "paid", "repeat", "cohort", "pmf",
                "transaction volume", "gmv", "active users", "engagement", "ranked", "volume"
            ],
            "rationale_high": "The notes include meaningful traction or product-market fit signals.",
            "rationale_low": "Revenue, retention, usage, and customer pull need stronger evidence.",
            "question": "What evidence shows product-market fit, retention, and repeatable demand?"
        },
        {
            "category": "Customer / ICP Clarity",
            "max_score": 10,
            "keywords": [
                "customer", "buyer", "user", "icp", "segment", "enterprise", "smb",
                "founders", "cfo", "legal", "finance", "operations", "consumer",
                "brands", "retailers", "restaurants", "qsr", "e-commerce", "app developers"
            ],
            "rationale_high": "The target customer segments are clear.",
            "rationale_low": "The primary buyer, user, and highest-urgency customer segment need clarification.",
            "question": "Who is the primary buyer, who is the daily user, and which segment has the strongest urgency?"
        },
        {
            "category": "Business Model / Unit Economics",
            "max_score": 10,
            "keywords": [
                "business model", "subscription", "saas", "usage-based", "marketplace",
                "gross margin", "cac", "payback", "ltv", "pricing", "revenue model",
                "unit economics", "monetization", "payout", "take rate"
            ],
            "rationale_high": "The business model is reasonably clear.",
            "rationale_low": "Pricing, margin structure, CAC, payback, and retention economics need more diligence.",
            "question": "What are the revenue model, gross margins, CAC, payback period, and retention economics?"
        },
        {
            "category": "GTM Scalability",
            "max_score": 8,
            "keywords": [
                "gtm", "sales", "pipeline", "channel", "distribution", "partnership",
                "outbound", "inbound", "plg", "enterprise sales", "customer acquisition",
                "self-serve", "sales motion", "go-to-market"
            ],
            "rationale_high": "The notes include some evidence of a scalable go-to-market motion.",
            "rationale_low": "The repeatability and scalability of the go-to-market motion need validation.",
            "question": "What acquisition channels are working, and can GTM scale beyond founder-led sales?"
        },
        {
            "category": "Competitive Positioning",
            "max_score": 7,
            "keywords": [
                "competitor", "competition", "incumbent", "alternative", "substitute",
                "moat", "defensible", "switching cost", "network effect", "copy",
                "traditional vendors", "data brokers", "platforms"
            ],
            "rationale_high": "The notes identify competitive dynamics and potential defensibility.",
            "rationale_low": "Competitive positioning and defensibility need more diligence.",
            "question": "Who are the strongest competitors or substitutes, and what prevents them from copying the product?"
        },
        {
            "category": "Risk / Legal / Compliance",
            "max_score": 5,
            "keywords": [
                "risk", "regulatory", "privacy", "security", "compliance", "legal",
                "concentration", "claims", "underwriting", "reinsurance", "data sharing",
                "consent", "trust", "fraud"
            ],
            "rationale_high": "The notes identify relevant risk areas for diligence.",
            "rationale_low": "Risk, legal, compliance, and concentration issues need more investigation.",
            "question": "What regulatory, legal, privacy, security, or concentration risks could break the thesis?"
        },
    ]

    scorecard = []

    for item in config:
        hits = _count_keyword_hits(notes, item["keywords"])
        score = _score_from_hits(hits, item["max_score"])

        if item["category"] == "Market Opportunity":
            if len(deal.customer_signals) >= 4:
                score = max(score, 10)
            if len(deal.traction_signals) >= 3:
                score = max(score, 10)
            if _count_keyword_hits(notes, ["large", "demand", "market", "enterprise", "consumer", "platform"]) >= 3:
                score = max(score, 11)

        if item["category"] == "Customer / ICP Clarity" and deal.customer_signals:
            score = max(score, 8)

        if item["category"] == "Traction / PMF Evidence" and deal.traction_signals:
            score = max(score, 10)

        if item["category"] == "Product / Differentiation" and _is_known(deal.description):
            score = max(score, 10)

        if item["category"] == "Business Model / Unit Economics" and _is_known(deal.business_model):
            score = max(score, 6)

        if item["category"] == "Competitive Positioning" and deal.risks:
            score = max(score, 4)

        if item["category"] == "Risk / Legal / Compliance" and deal.risks:
            score = max(score, 4)

        evidence = _evidence_level(score, item["max_score"])
        rationale = item["rationale_high"] if evidence in {"High", "Medium"} else item["rationale_low"]

        scorecard.append(
            DiligenceScorecardItem(
                category=item["category"],
                score=score,
                max_score=item["max_score"],
                evidence_level=evidence,
                rationale=rationale,
                diligence_question=item["question"]
            )
        )

    return scorecard


def generate_priority_diligence_questions(
    deal: DealRecord,
    scorecard: List[DiligenceScorecardItem],
    max_questions: int = 8
) -> List[str]:
    questions = []

    for question in deal.diligence_questions:
        normalized = _normalize_question(question)
        if normalized and normalized not in questions:
            questions.append(normalized)

    sorted_scorecard = sorted(
        scorecard,
        key=lambda item: item.score / item.max_score if item.max_score else 0
    )

    for item in sorted_scorecard:
        if item.diligence_question and item.diligence_question not in questions:
            questions.append(item.diligence_question)

        if len(questions) >= max_questions:
            break

    return questions[:max_questions]


def calculate_confidence_score(deal: DealRecord, raw_notes: str, scorecard: List[DiligenceScorecardItem]) -> int:
    notes = _clean_text(raw_notes)

    key_fields = [
        deal.company_name,
        deal.sector,
        deal.subsector,
        deal.business_model,
        deal.stage,
        deal.description,
        deal.recommended_next_step,
    ]

    known_fields = sum(1 for field in key_fields if _is_known(field))
    field_score = round((known_fields / len(key_fields)) * 35)

    list_items = (
        len(deal.traction_signals)
        + len(deal.customer_signals)
        + len(deal.funding_signals)
        + len(deal.risks)
        + len(deal.diligence_questions)
    )
    signal_score = min(30, list_items * 3)

    notes_score = min(20, len(notes) // 150)

    evidence_values = {
        "High": 15,
        "Medium": 10,
        "Low": 5,
        "Insufficient": 0,
        "Unknown": 0,
    }

    evidence_score = 0
    if scorecard:
        evidence_score = round(
            sum(evidence_values.get(item.evidence_level, 0) for item in scorecard)
            / len(scorecard)
        )

    confidence = field_score + signal_score + notes_score + evidence_score
    confidence = max(0, min(100, confidence))

    # Confidence should reflect evidence completeness, not verified truth.
    # If no source links/citations are provided, cap the score.
    if not _has_source_link(raw_notes):
        confidence = min(confidence, 90)

    # If notes are very short, cap confidence more aggressively.
    if len(notes) < 800:
        confidence = min(confidence, 80)

    return confidence


def determine_priority(opportunity_score: int, confidence_score: int) -> str:
    if opportunity_score >= 85 and confidence_score >= 70:
        return "High Priority"

    if opportunity_score >= 75:
        return "Medium / High Priority"

    if opportunity_score >= 60:
        return "Needs More Diligence"

    if opportunity_score >= 40:
        return "Low Priority"

    return "Pass / Insufficient Info"


def apply_vc_scorecard(deal: DealRecord, raw_notes: str) -> DealRecord:
    scorecard = build_due_diligence_scorecard(deal, raw_notes)

    opportunity_score = sum(item.score for item in scorecard)
    opportunity_score = max(0, min(100, opportunity_score))

    confidence_score = calculate_confidence_score(deal, raw_notes, scorecard)

    deal.diligence_scorecard = scorecard
    deal.opportunity_score = opportunity_score
    deal.confidence_score = confidence_score
    deal.priority = determine_priority(opportunity_score, confidence_score)
    deal.diligence_questions = generate_priority_diligence_questions(deal, scorecard)

    if not _is_known(deal.recommended_next_step):
        lowest_categories = sorted(
            scorecard,
            key=lambda item: item.score / item.max_score if item.max_score else 0
        )[:3]

        focus_areas = ", ".join(item.category.lower() for item in lowest_categories)

        deal.recommended_next_step = (
            f"Conduct follow-up diligence on {focus_areas}, then validate whether the opportunity "
            "has enough evidence to move forward."
        )

    return deal


def fallback_deal_record(raw_notes: str) -> DealRecord:
    company_name = _extract_company_name(raw_notes)

    deal = DealRecord(
        company_name=company_name,
        sector="Unknown",
        subsector="Unknown",
        business_model="Unknown",
        stage="Unknown",
        description="LLM extraction was unavailable. Review the notes manually or check API configuration.",
        traction_signals=[],
        customer_signals=[],
        funding_signals=[],
        risks=["Requires manual review"],
        diligence_questions=[
            "What does the company do?",
            "Who are the customers?",
            "What traction has the company achieved?",
            "What is the business model?",
            "What are the main risks?"
        ],
        crm_tags=["Needs Review"],
        relationship_context="Source context unavailable.",
        recommended_next_step="Request additional company materials and rerun the analysis.",
        opportunity_score=0,
        confidence_score=0,
        priority="Pass / Insufficient Info",
        prompt_version="v1.1-diligence-scorecard"
    )

    return apply_vc_scorecard(deal, raw_notes)