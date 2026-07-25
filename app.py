import streamlit as st
from dotenv import load_dotenv

from src.analysis_service import analyze_deal
from src.export import create_pipeline_dataframe
from src.sample_data import REAL_SAMPLE_DEALS
from src.ui.components import render_result
from src.ui.memo_view import render_investment_memo_workspace
from src.ui.styles import inject_css

load_dotenv()

st.set_page_config(
    page_title="DealFlow AI",
    page_icon="DF",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


def initialize_state() -> None:
    defaults = {
        "deals": [],
        "deal_inputs": [],
        "company_name": "",
        "source_type": "Research notes",
        "investment_focus": "",
        "company_notes": "",
        "latest_deal": None,
        "analysis_complete": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_workspace() -> None:
    for key, value in {
        "company_name": "",
        "source_type": "Research notes",
        "investment_focus": "",
        "company_notes": "",
        "latest_deal": None,
        "analysis_complete": False,
    }.items():
        st.session_state[key] = value


def clear_pipeline() -> None:
    st.session_state["deals"] = []
    st.session_state["deal_inputs"] = []
    st.session_state.pop("memo_selected_deal", None)
    st.session_state.pop("investment_memo_selected_deal", None)
    clear_workspace()


def load_sample(sample_name: str) -> None:
    st.session_state["company_name"] = sample_name.split(" - ")[0]
    st.session_state["source_type"] = "Research notes"
    st.session_state["investment_focus"] = "Private-market screening"
    st.session_state["company_notes"] = REAL_SAMPLE_DEALS[sample_name]


def run_analysis() -> None:
    raw_notes = f"""
Company name: {st.session_state.company_name}
Source type: {st.session_state.source_type}
Investment focus: {st.session_state.investment_focus}

Company notes:
{st.session_state.company_notes}
""".strip()

    with st.spinner(
        "Analyzing notes and building the evidence scorecard..."
    ):
        result = analyze_deal(raw_notes)

    st.session_state.latest_deal = result.deal
    st.session_state.deals.append(result.deal)
    st.session_state.deal_inputs.append(raw_notes)
    st.session_state["memo_selected_deal"] = (
        len(st.session_state.deals) - 1
    )
    st.session_state["investment_memo_selected_deal"] = (
        len(st.session_state.deals) - 1
    )
    st.session_state.analysis_complete = True


initialize_state()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-title">DealFlow AI</div>
          <div class="sidebar-sub">
            Private-market diligence workspace
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Workflow")

    st.markdown(
        "1. Load or paste company notes\n"
        "2. Extract structured evidence\n"
        "3. Review evidence coverage\n"
        "4. Prioritize diligence gaps\n"
        "5. Export a deal record or memo"
    )

    st.divider()

    total = len(st.session_state.deals)

    ready = sum(
        deal.priority == "Diligence Ready"
        for deal in st.session_state.deals
    )

    st.metric("Deals in session", total)
    st.metric("Diligence ready", ready)

    st.divider()

    st.button(
        "Clear workspace",
        width="stretch",
        on_click=clear_workspace,
    )

    st.button(
        "Clear pipeline",
        width="stretch",
        on_click=clear_pipeline,
    )


st.title("DealFlow AI")

st.caption(
    "Convert unstructured company notes into a structured evidence review, "
    "diligence questions, CRM-ready data, and an investment memo."
)

tab_deal, tab_pipeline, tab_memo = st.tabs(
    [
        "Deal Intake",
        "Pipeline",
        "Investment Memo",
    ]
)


with tab_deal:
    left, right = st.columns(
        [0.38, 0.62],
        gap="large",
    )

    with left:
        st.markdown(
            '<div class="section-title">Deal intake</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Use sample mode for a public demo without preparing notes."
        )

        sample_name = st.selectbox(
            "Sample deal",
            ["Select a sample"] + list(REAL_SAMPLE_DEALS),
        )

        if st.button(
            "Load sample",
            width="stretch",
            disabled=sample_name == "Select a sample",
        ):
            load_sample(sample_name)
            st.rerun()

        st.text_input(
            "Company name",
            key="company_name",
        )

        st.selectbox(
            "Source type",
            [
                "Research notes",
                "Company website text",
                "Funding announcement",
                "Founder call notes",
                "Investor update",
                "Other",
            ],
            key="source_type",
        )

        st.text_input(
            "Optional investment focus",
            key="investment_focus",
        )

        st.text_area(
            "Company notes",
            key="company_notes",
            height=380,
            placeholder=(
                "Include product, customer, traction, pricing, market, "
                "competition, and risk evidence."
            ),
        )

        if st.button(
            "Analyze deal",
            width="stretch",
        ):
            if len(st.session_state.company_notes.strip()) < 100:
                st.warning(
                    "Provide at least 100 characters of company context."
                )
            else:
                try:
                    run_analysis()
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with right:
        st.markdown(
            '<div class="section-title">Evidence review</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Evidence completeness is not an investment recommendation "
            "or valuation signal."
        )

        latest = st.session_state.latest_deal

        if latest is None:
            st.info(
                "Load a sample deal or paste notes to generate the "
                "evidence scorecard."
            )

            sample_preview = next(iter(REAL_SAMPLE_DEALS))

            st.markdown(
                f"**Suggested demo:** {sample_preview}"
            )
        else:
            render_result(latest)


with tab_pipeline:
    st.markdown(
        '<div class="section-title">Session pipeline</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Analyzed deals remain in the current browser session and can "
        "be exported as CSV."
    )

    if not st.session_state.deals:
        st.info("No analyzed companies yet.")
    else:
        dataframe = create_pipeline_dataframe(
            st.session_state.deals
        )

        display_columns = [
            "company_name",
            "sector",
            "stage",
            "evidence_completeness_score",
            "diligence_status",
            "extraction_confidence",
            "analysis_path",
            "recommended_next_step",
        ]

        visible_columns = [
            column
            for column in display_columns
            if column in dataframe
        ]

        st.dataframe(
            dataframe[visible_columns],
            width="stretch",
            hide_index=True,
        )

        with st.expander("Full export preview"):
            st.dataframe(
                dataframe,
                width="stretch",
                hide_index=True,
            )

        st.download_button(
            "Download CRM-ready CSV",
            data=dataframe.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="dealflow_pipeline_export.csv",
            mime="text/csv",
        )


with tab_memo:
    render_investment_memo_workspace(
        deals=st.session_state.deals,
        deal_inputs=st.session_state.deal_inputs,
    )