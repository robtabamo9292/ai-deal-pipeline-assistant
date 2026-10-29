"""Transparent source-text matching; this is NOT semantic or factual verification."""
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
