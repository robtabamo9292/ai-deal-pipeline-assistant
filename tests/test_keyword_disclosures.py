"""Regression tests: keyword-only text and deferred information earn no evidence."""
import base64
import re
import zlib

import pytest

from src.demo import curated_northstar_example
from src.memo import generate_investment_memo
from src.memo_pdf_v2 import memo_to_pdf_bytes
from src.sample_data import DEFAULT_SAMPLE_DEAL_NOTES
from src.schema import DealRecord
from src.scoring import _has_any, apply_vc_scorecard


def _notes_score(notes: str) -> int:
    """Score from the notes alone (no extracted fields)."""
    return apply_vc_scorecard(DealRecord(), notes).opportunity_score


def test_keyword_salad_with_a_common_verb_scores_zero():
    # Previously scored 70: the word "use" (from "use case") satisfied the
    # disclosure check for the whole run-on keyword list.
    salad = (
        "founder ceo background experience track record market size tam why now "
        "workflow integration proprietary moat network effect retention cohort "
        "buyer use case pricing subscription gross margin cac expansion upsell "
        "go-to-market pipeline conversion partner self-serve competitor "
        "differentiation regulatory churn runway"
    )
    assert _notes_score(salad) == 0


def test_keyword_sentences_without_facts_score_zero():
    # Previously scored 46.
    notes = (
        "The founder has experience and a track record. "
        "The market has TAM and a why now. "
        "Pricing is subscription with gross margin and CAC payback. "
        "GTM uses pipeline, outbound and partners. "
        "Competitors include incumbents."
    )
    assert _notes_score(notes) == 0


@pytest.mark.parametrize(
    "sentence",
    [
        "Pricing is TBD pending the next call.",
        "Founder experience is to be confirmed by references.",
        "Market size is a placeholder until diligence.",
        "Gross margin and CAC payback are pending diligence.",
        "Competitor mapping is TBC after the partner meeting.",
    ],
)
def test_deferred_information_counts_as_missing(sentence):
    # "Founder experience is to be confirmed" previously earned 11 team points.
    assert _notes_score(sentence) == 0


@pytest.mark.parametrize(
    ("sentence", "phrases"),
    [
        ("Founder has 10 years of domain experience.", ["founder"]),
        ("Gross margin is 78% with a 14-month CAC payback.", ["gross margin"]),
        ("Competitors include EHR modules and manual outsourcing firms.", ["competitors"]),
        ("Risks include HIPAA compliance and EHR integration complexity.", ["compliance"]),
        ("Net retention is 118% across the 2024 cohort.", ["retention"]),
        (
            "Founder-led outbound sales with channel experiments through "
            "billing-services partners.",
            ["outbound"],
        ),
    ],
)
def test_specific_disclosures_still_count(sentence, phrases):
    assert _has_any(sentence, phrases)


def _pdf_text(pdf: bytes) -> bytes:
    """Decode ReportLab's ASCII85 + Flate content streams."""
    text = b""
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", pdf, re.S):
        data = match.group(1).strip()
        try:
            text += zlib.decompress(base64.a85decode(data, adobe=True))
        except (ValueError, zlib.error):
            continue
    return text


def test_pdf_uses_clear_metric_labels():
    # Previously the record-completeness value was labeled "COVERAGE",
    # next to a separate "EVIDENCE" score.
    deal = curated_northstar_example(DEFAULT_SAMPLE_DEAL_NOTES)
    text = _pdf_text(memo_to_pdf_bytes(generate_investment_memo(deal)))
    assert b"(EVIDENCE COVERAGE)" in text
    assert b"(REVIEW STATUS)" in text
    assert b"(RECORD COMPLETENESS)" in text
    assert b"(COVERAGE)" not in text
