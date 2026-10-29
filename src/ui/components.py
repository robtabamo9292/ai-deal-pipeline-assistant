from html import escape

import pandas as pd
import streamlit as st

from src.export import create_pipeline_dataframe


def clean_text(value, fallback="—") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "; ".join(items) if items else fallback
    text = str(value).strip()
    return text if text and text.lower() != "unknown" else fallback


def clean_list(values) -> list[str]:
    return [
        str(value).strip()
        for value in values or []
        if str(value).strip().lower()
        not in {"", "unknown", "none", "n/a", "not provided"}
    ]


def scorecard_dataframe(scorecard) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Category": item.category,
                "Evidence Score": item.score,
                "Maximum": item.max_score,
                "Coverage %": round(item.score / item.max_score * 100) if item.max_score else 0,
                "Coverage": item.evidence_level,
                "What the score means": item.rationale,
                "Priority diligence question": item.diligence_question,
            }
            for item in scorecard or []
        ]
    )


def render_metrics(deal) -> None:
    scorecard = deal.diligence_scorecard or []
    strong = sum(item.evidence_level == "Strong" for item in scorecard)
    covered = sum(
        item.evidence_level in {"Strong", "Partial"}
        for item in scorecard
    )
    cards = [
        (
            "Evidence completeness",
            "Not scored" if deal.fallback_used else f"{deal.opportunity_score}/100",
            f"{covered} of {len(scorecard)} categories covered",
        ),
        (
            "Diligence status",
            clean_text(deal.priority),
            "Not an investment recommendation",
        ),
        (
            "Record completeness",
            "Not scored" if deal.fallback_used else f"{deal.confidence_score}/100",
            "Field coverage, not verified truth",
        ),
        (
            "Strong evidence",
            str(strong),
            "Categories with documented support",
        ),
    ]
    columns = st.columns(4)
    for column, (label, value, subtext) in zip(columns, cards):
        width = deal.opportunity_score if label == "Evidence completeness" else 0
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="metric-label">{escape(label)}</div>
                  <div class="metric-value">{escape(value)}</div>
                  <div class="metric-sub">{escape(subtext)}</div>
                  <div class="evidence-bar"><div class="evidence-fill" style="width:{width}%"></div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_provenance(deal) -> None:
    warning = (
        f" · {escape(deal.analysis_warning)}"
        if deal.analysis_warning
        else ""
    )
    st.markdown(
        f"""
        <div class="status-strip">
          Analysis path: <strong>{escape(deal.analysis_path)}</strong> ·
          Model: <strong>{escape(deal.model_name)}</strong> ·
          Methodology: <strong>{escape(deal.score_methodology)}</strong> ·
          Prompt: <strong>{escape(deal.prompt_version)}</strong>{warning}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(deal) -> None:
    if deal.fallback_used:
        st.warning(
            "AI extraction did not run. No investment evidence was scored; "
            "configure the AI service or use the curated offline demo."
        )
        render_provenance(deal)
        return
    render_metrics(deal)
    render_provenance(deal)

    scorecard_tab, summary_tab, risks_tab, sources_tab, fields_tab, export_tab = st.tabs(
        [
            "Evidence Scorecard",
            "Executive Summary",
            "Risks & Questions",
            "Source Excerpts",
            "Structured Fields",
            "Export",
        ]
    )

    with scorecard_tab:
        st.caption(
            "This score measures evidence completeness across diligence "
            "categories. It does not predict investment returns or replace "
            "investment judgment."
        )
        dataframe = scorecard_dataframe(deal.diligence_scorecard)
        if dataframe.empty:
            st.info("No scorecard generated.")
        else:
            st.dataframe(
                dataframe,
                width="stretch",
                hide_index=True,
                column_config={
                    "Coverage %": st.column_config.ProgressColumn(
                        "Coverage %",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    )
                },
            )

    with summary_tab:
        st.subheader("Company overview — extracted from notes")
        st.write(clean_text(deal.description))
        st.subheader("Recommended next step")
        st.write(clean_text(deal.recommended_next_step))
        left, right = st.columns(2)
        with left:
            st.markdown("#### Documented traction")
            items = clean_list(deal.traction_signals) or [
                "No supported traction evidence provided."
            ]
            for item in items:
                st.markdown("- " + item.replace("$", r"\$"))
        with right:
            st.markdown("#### Customer evidence")
            items = clean_list(deal.customer_signals) or [
                "No supported customer evidence provided."
            ]
            for item in items:
                st.markdown("- " + item.replace("$", r"\$"))

    with risks_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Key risks")
            for index, item in enumerate(clean_list(deal.risks), start=1):
                with st.expander(f"Risk {index}: {item[:90]}"):
                    st.write(item)
        with right:
            st.markdown("#### Priority diligence questions")
            questions = clean_list(deal.diligence_questions)
            for index, item in enumerate(questions, start=1):
                with st.expander(f"Question {index}: {item[:90]}"):
                    st.write(item)

    with sources_tab:
        st.caption(
            "A matched quotation only establishes that words appear in the "
            "submitted notes. Whether the passage supports a claim, or "
            "whether the claim is true, requires separate review."
        )
        if deal.source_matches:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Category": match.category,
                        "Extracted claim": match.claim,
                        "Quoted source text": match.quote,
                        "Text match": "Found" if match.exact_text_match else "Not found",
                        "Review status": match.review_status,
                    }
                    for match in deal.source_matches
                ]),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No source quotations were returned for this analysis.")

    with fields_tab:
        fields = {
            "Company Name": deal.company_name,
            "Sector": deal.sector,
            "Subsector": deal.subsector,
            "Business Model": deal.business_model,
            "Stage": deal.stage,
            "Diligence Status": deal.priority,
            "Evidence Completeness": deal.opportunity_score,
            "Record Completeness": deal.confidence_score,
            "Source Context": deal.relationship_context,
            "CRM Tags": clean_text(deal.crm_tags),
        }
        st.dataframe(
            pd.DataFrame(fields.items(), columns=["Field", "Value"]),
            width="stretch",
            hide_index=True,
        )

    with export_tab:
        preview = create_pipeline_dataframe([deal])
        st.dataframe(preview, width="stretch", hide_index=True)
        st.download_button(
            "Download this deal CSV",
            data=preview.to_csv(index=False).encode("utf-8"),
            file_name=(
                f"{clean_text(deal.company_name, 'deal').replace(' ', '_').lower()}"
                "_deal_record.csv"
            ),
            mime="text/csv",
        )
