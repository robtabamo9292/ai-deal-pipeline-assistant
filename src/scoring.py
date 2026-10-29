import re
from typing import Iterable, List

from src.schema import DealRecord, DiligenceScorecardItem


UNKNOWN_VALUES = {
    "", "unknown", "n/a", "none", "not provided", "not available",
    "not disclosed", "undisclosed", "unspecified", "no information",
    "not yet known", "needs review", "requires review",
    "tbd", "tbc", "to be confirmed", "to be determined", "pending",
}

# Phrases that mean information is absent or deferred, beyond plain negation.
_DEFERRED = (
    r"tbd|tbc|to be (?:confirmed|determined|provided|shared|verified|validated)|"
    r"pending (?:confirmation|diligence|research|review|verification|the next)|"
    r"placeholder|unconfirmed|not yet"
)

# Every word used by the rubric's evidence phrases, plus common filler. A
# clause made almost entirely of these words names diligence topics without
# stating facts about the company.
_RUBRIC_VOCABULARY = set(
    """
    founder co-founder ceo management team background experience domain expertise
    previously track record prior exit repeat operator market size tam addressable
    budget why now tailwind tailwinds urgent regulatory driver workflow integration
    proprietary differentiation switching cost network effect data advantage moat
    retention cohort renewal usage buyer economic decision maker use case pain point
    job done pricing subscription usage-based take rate gross margin cac payback ltv
    expansion upsell net go-to-market gtm sales channel distribution pipeline
    conversion cycle outbound inbound partner self-serve product-led plg competitor
    competitors competition incumbent alternative defensible privacy security
    compliance legal concentration churn runway execution risk risks strong large
    good great clear solid evidence information details metrics company startup
    product customers customer traction model business
    """.split()
)

_STOPWORDS = set(
    """
    a an the and or of to in on for with by at as from into is are was were be been
    has have had it its this that these those there their our we they he she his
    her also very and/or plus both each all any some such than then so
    use uses using include includes including provide provides offer offers
    via through across
    """.split()
)


def _in_vocabulary(word: str) -> bool:
    return word in _RUBRIC_VOCABULARY or word.rstrip("s") in _RUBRIC_VOCABULARY


def _is_fact_bearing(clause: str) -> bool:
    """
    True when a clause states something specific about the company.

    Requires a figure, a named entity or acronym (e.g. "Salesforce", "CFO"),
    or at least two content words outside the rubric vocabulary, and rejects
    clauses that are mostly rubric keywords.
    """
    # Ignore a leading heading such as "Go-to-market:"; it is formatting.
    body = re.sub(r"^\s*[A-Za-z][\w /&-]{0,30}:\s*", "", clause)
    tokens = [token.strip(".,'") for token in re.findall(r"[A-Za-z0-9$%][\w$%.,'-]*", body)]
    content = [token for token in tokens if token and token.lower() not in _STOPWORDS]
    if not content:
        return False
    outside = [token for token in content if not _in_vocabulary(token.lower())]
    has_figure = any(re.search(r"\d", token) for token in content)
    # A specific company, product or role: capitalized mid-sentence, or an
    # acronym such as CFO or HIPAA. Sentence-initial capitals do not count.
    has_entity = any(
        not _in_vocabulary(token.lower())
        and token.lower() not in _STOPWORDS
        and (
            (len(token) >= 2 and token.isupper() and token.isalpha())
            or (index > 0 and token[:1].isupper())
        )
        for index, token in enumerate(tokens)
    )
    vocabulary_share = 1 - len(outside) / len(content)
    if vocabulary_share > 0.7 and not has_figure:
        return False
    return has_figure or has_entity or len(outside) >= 2


def _clean_text(value) -> str:
    return str(value or "").strip()


def _is_known(value) -> bool:
    return _clean_text(value).lower() not in UNKNOWN_VALUES


def _known_items(values: Iterable[object]) -> list[str]:
    return [str(value).strip() for value in values or [] if _is_known(value)]


def _has_any(text: str, phrases: Iterable[str]) -> bool:
    """Conservative evidence hint: require a meaningful, non-missing disclosure.

    This is a heuristic for legacy records, NOT source-verification. It prevents
    substring collisions (TAM/Amsterdam, CAC/cacao), missing-information
    sentences, and bare keyword lists from earning evidence points.
    """
    if not text:
        return False
    expression = re.compile(
        r"(?<![\w])(?:" + "|".join(re.escape(p) for p in phrases) + r")(?![\w])",
        re.IGNORECASE,
    )
    missing = re.compile(
        r"\b(?:no|none|not|without|missing|unknown|undisclosed|"
        r"unavailable|unreported|unspecified|lacking|lack|absent|" + _DEFERRED + r")\b",
        re.IGNORECASE,
    )
    disclosure = re.compile(
        r"\b(?:is|are|was|were|has|have|had|grew|declined|"
        r"includes?|provides?|offers?|sells?|builds?|targets?|uses?|"
        r"raised|launched|reported|generates?|faces?|requires?|"
        r"signed|operates?|serves?|automates?|addresses?|drives?|"
        r"achieved|works?|combines?|priced|founded|completed|"
        r"measures?|estimated|led|partners?|customers?)\b",
        re.IGNORECASE,
    )
    for sentence in re.split(r"(?<=[.!?])\s+|[\r\n;]+", text):
        for clause in re.split(r"\b(?:but|however|although|whereas)\b", sentence, flags=re.IGNORECASE):
            if not expression.search(clause) or missing.search(clause):
                continue
            # Bare headings/keyword collections are not business disclosures.
            if len(re.findall(r"\b[\w-]+\b", clause)) < 4:
                continue
            # Keyword lists and keyword sentences ("the founder has experience
            # and a track record") name topics without stating facts.
            if not _is_fact_bearing(clause):
                continue
            if disclosure.search(clause) or re.search(r"[$%\d]", clause):
                return True
    return False


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
    from src.verification import match_source_excerpts

    # Matching a quote does not verify its semantics or external truth.
    deal.source_matches = match_source_excerpts(deal.evidence_excerpts, raw_notes)
    scorecard = build_due_diligence_scorecard(deal, raw_notes)
    deal.diligence_scorecard = scorecard
    deal.opportunity_score = max(0, min(100, sum(item.score for item in scorecard)))
    deal.confidence_score = calculate_confidence_score(deal, raw_notes, scorecard)
    deal.priority = determine_priority(deal.opportunity_score, deal.confidence_score)
    deal.diligence_questions = generate_priority_diligence_questions(deal, scorecard)
    deal.score_methodology = "evidence-completeness-v2"
    # Prompt version is owned by the extraction path, not the scorecard.
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
    """An unavailable AI analysis is *not* scored as investment evidence."""
    return DealRecord(
        company_name=_extract_company_name(raw_notes),
        crm_tags=["Needs Review"],
        recommended_next_step="Configure the AI service or review the notes manually.",
        priority="Not analyzed",
        analysis_path="deterministic_fallback",
        fallback_used=True,
        analysis_warning="AI extraction was unavailable; no evidence score was calculated.",
        model_name="none",
        score_methodology="not-scored",
        prompt_version="not-run",
    )
