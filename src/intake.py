"""Keep application metadata separate from the evidence being scored."""


def source_notes_for_analysis(
    notes: str,
    *,
    company_name: str = "",
    source_type: str = "",
    investment_focus: str = "",
) -> str:
    """Return only supplied evidence; metadata never enters the scoring text."""
    del company_name, source_type, investment_focus
    source = (notes or "").strip()
    if not source:
        raise ValueError("Company notes cannot be empty.")
    return source
