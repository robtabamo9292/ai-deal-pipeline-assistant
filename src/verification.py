"""Transparent source-text matching; this is NOT semantic or factual verification."""
import math
import re

from src.schema import EvidenceExcerpt, SourceMatch


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()


def match_source_excerpts(
    excerpts: list[EvidenceExcerpt], source_notes: str
) -> list[SourceMatch]:
    """Check whether verbatim model-proposed quotations occur in supplied notes.

    A text match means *only* that the words appear in the uploaded source.
    It does NOT establish that the quote logically supports the claim or that
    the underlying assertion is true. All matches require analyst review.
    """
    source = normalized_text(source_notes)
    out = []
    for excerpt in excerpts:
        quote = normalized_text(excerpt.quote)
        match = len(quote) >= 8 and quote in source
        out.append(
            SourceMatch(
                category=excerpt.category,
                claim=excerpt.claim,
                quote=excerpt.quote,
                exact_text_match=match,
                review_status=(
                    "Quote found — assess claim support"
                    if match
                    else "Quote not found — reject or correct"
                ),
            )
        )
    return out


# --- Signal support -------------------------------------------------------
#
# Model-extracted signals (traction, customers, risks) are paraphrases, so an
# exact substring test would reject almost all of them. The check below is a
# transparent token test instead: a signal is "source-supported" when every
# figure it states appears in the notes and most of its content words do.
# Like quote matching, this shows the words are present, not that the claim
# is true.

_SIGNAL_STOPWORDS = set(
    """
    a an the and or of to in on for with by at as from into is are was were be
    been has have had it its this that these those their our we they also very
    over per than then so via through across about up down out all any some
    each both plus including include includes such
    """.split()
)

_MULTIPLIERS = {
    "k": 1e3, "thousand": 1e3,
    "m": 1e6, "mm": 1e6, "million": 1e6,
    "b": 1e9, "bn": 1e9, "billion": 1e9,
}

_FIGURE = re.compile(
    r"(\d+(?:,\d{3})*(?:\.\d+)?)"
    r"(?:\s?(k|mm|m|bn|b|thousand|million|billion)(?![a-z]))?"
    r"(\s?%)?",
    re.IGNORECASE,
)

# A content word must cover at least this share of a figure-free signal.
SIGNAL_WORD_COVERAGE = 2 / 3


def _figures(text: str) -> set[tuple[float, bool]]:
    """Numbers in text as (value, is_percent), so $420K matches $420,000."""
    out = set()
    for number, suffix, percent in _FIGURE.findall(text or ""):
        value = float(number.replace(",", ""))
        value *= _MULTIPLIERS.get(suffix.lower(), 1) if suffix else 1
        out.add((round(value, 6), bool(percent)))
    return out


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z']+", (text or "").casefold())
    return {
        word.rstrip("s") or word
        for word in words
        if len(word) > 2 and word not in _SIGNAL_STOPWORDS
    }


def is_source_supported(signal: str, source_notes: str) -> bool:
    """True when the signal's figures and most of its words occur in the notes."""
    signal_text = normalized_text(signal)
    source = normalized_text(source_notes)
    if not signal_text or not source:
        return False
    if signal_text in source:
        return True

    signal_figures = _figures(signal_text)
    if signal_figures and not signal_figures <= _figures(source):
        return False

    words = _content_words(signal_text)
    if not words:
        return bool(signal_figures)
    found = words & _content_words(source)
    if signal_figures:
        # The figure carries the claim; one shared word ties it to a topic.
        return len(found) >= 1
    return len(found) >= max(1, math.ceil(len(words) * SIGNAL_WORD_COVERAGE))


def split_supported(
    signals: list[str], source_notes: str
) -> tuple[list[str], list[str]]:
    """Partition signals into (source-supported, not found in notes)."""
    supported, unsupported = [], []
    for signal in signals:
        (supported if is_source_supported(signal, source_notes) else unsupported).append(signal)
    return supported, unsupported
