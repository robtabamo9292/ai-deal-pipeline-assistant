from collections.abc import Sequence
from html import escape

import streamlit as st

from src.memo import generate_investment_memo
from src.memo_pdf_v2 import memo_to_pdf_bytes
from src.schema import DealRecord
from src.ui.components import clean_text, render_metrics


def _plain_text(value: object, fallback: str = "Not provided") -> str:
    return clean_text(value, fallback).replace("`", "").replace("$", r"\$")


def _render_plain_paragraph(
    value: object,
    fallback: str = "Not provided",
) -> None:
    text = clean_text(value, fallback).replace("`", "")
    safe_text = escape(text).replace("\n", "<br>")
    st.markdown(
        f"<p style=\"margin: 0 0 1rem 0; line-height: 1.6;\">{safe_text}</p>",
        unsafe_allow_html=True,
    )


def _render_list(items: Sequence[str], empty_message: str) -> None:
    cleaned_items = [
        _plain_text(item, "")
        for item in items
        if _plain_text(item, "")
        and _plain_text(item, "").lower() != "unknown"
    ]

    if not cleaned_items:
        st.caption(empty_message)
        return

    for item in cleaned_items:
        st.markdown(f"- {item}")


def _safe_filename(value: str) -> str:
    cleaned = _plain_text(value, "deal")
    return (
        cleaned.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .lower()
    )


def render_investment_memo_workspace(
    deals: Sequence[DealRecord],
    deal_inputs: Sequence[str],
) -> None:
    st.markdown(
        '<div class="section-title">Investment memo</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Review the complete diligence record and export a one-page "
        "screening brief."
    )

    if not deals:
        st.info("Analyze a deal before generating an investment memo.")
        return

    names = [
        _plain_text(deal.company_name, f"Deal {index + 1}")
        for index, deal in enumerate(deals)
    ]

    default_index = st.session_state.get(
        "memo_selected_deal",
        len(names) - 1,
    )
    default_index = max(0, min(default_index, len(names) - 1))

    selected_index = st.selectbox(
        "Select a deal",
        options=list(range(len(names))),
        index=default_index,
        format_func=lambda index: names[index],
        key="investment_memo_selected_deal",
    )

    selected_deal = deals[selected_index]
    selected_notes = (
        deal_inputs[selected_index]
        if selected_index < len(deal_inputs)
        else ""
    )

    memo = generate_investment_memo(
        selected_deal,
        selected_notes,
    )

    render_metrics(selected_deal)

    st.divider()

    header_left, header_right = st.columns([0.7, 0.3])

    with header_left:
        st.subheader(_plain_text(memo.company_name))
        st.caption(
            f"{_plain_text(memo.sector)}"
            f" | {_plain_text(memo.subsector)}"
            f" | {_plain_text(memo.stage)}"
        )

    with header_right:
        st.markdown(
            f"**Diligence status:** {_plain_text(memo.priority)}"
        )
        st.markdown(
            f"**Evidence completeness:** "
            f"{memo.opportunity_score}/100"
        )
        st.markdown(
            f"**Extraction confidence:** "
            f"{memo.confidence_score}/100"
        )

    st.divider()

    st.subheader("Executive summary")
    _render_plain_paragraph(memo.executive_summary)

    st.subheader("Company overview")
    _render_plain_paragraph(memo.company_overview)

    st.subheader("Investment thesis")
    _render_list(
        memo.investment_thesis,
        "The submitted notes do not yet support a complete thesis.",
    )

    st.subheader("Traction, customers, and funding")
    _render_plain_paragraph(memo.traction_and_customers)

    risk_column, question_column = st.columns(2, gap="large")

    with risk_column:
        st.subheader("Key risks")
        _render_list(
            memo.key_risks,
            "Risk evidence was not provided in the submitted notes.",
        )

    with question_column:
        st.subheader("Priority diligence questions")
        _render_list(
            memo.diligence_questions,
            "No diligence questions were generated.",
        )

    st.subheader("Recommended next steps")
    _render_list(
        memo.recommended_next_steps,
        "No next step was documented.",
    )

    st.divider()
    st.subheader("Exports")

    one_page_pdf = memo_to_pdf_bytes(memo)
    safe_name = _safe_filename(names[selected_index])

    st.download_button(
        "Download one-page screening brief",
        data=one_page_pdf,
        file_name=f"{safe_name}_screening_brief.pdf",
        mime="application/pdf",
        width="stretch",
    )