import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent_workflow import analyze_deal_with_agents
from src.llm import analyze_deal_with_llm
from src.export import create_pipeline_dataframe
from src.sample_data import REAL_SAMPLE_DEALS


load_dotenv()


st.set_page_config(
    page_title="DealFlow AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)


def safe_text(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if str(v).strip()) or "—"
    return str(value).replace("$", "\\$") or "—"


def inject_css():
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }

        .stApp {
            background: #070b16;
            color: #e6edf7;
        }

        .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            max-width: 1500px !important;
        }

        section[data-testid="stSidebar"] {
            background: #080f1f;
            border-right: 1px solid rgba(105, 124, 170, 0.22);
        }

        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: #e6edf7;
        }

        .muted {
            color: #8f9bb3 !important;
            font-size: 0.92rem;
        }

        .brand-card {
            background: linear-gradient(135deg, rgba(72, 101, 255, 0.18), rgba(15, 23, 42, 0.92));
            border: 1px solid rgba(100, 125, 255, 0.28);
            border-radius: 18px;
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
        }

        .brand-title {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .brand-sub {
            color: #95a2ba;
            font-size: 0.85rem;
            margin-top: 0.15rem;
        }

        .panel {
            background: #091120;
            border: 1px solid rgba(105, 124, 170, 0.24);
            border-radius: 18px;
            padding: 1.1rem 1.15rem;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
            margin-bottom: 1rem;
        }

        .panel-title {
            font-size: 1.05rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .metric-card {
            background: #0b1425;
            border: 1px solid rgba(105, 124, 170, 0.25);
            border-radius: 16px;
            padding: 1rem;
            min-height: 110px;
        }

        .metric-label {
            color: #8f9bb3 !important;
            font-size: 0.82rem;
            margin-bottom: 0.55rem;
        }

        .metric-value {
            font-size: 1.7rem;
            font-weight: 850;
            letter-spacing: -0.04em;
        }

        .metric-sub {
            color: #2ee985 !important;
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }

        .stTextInput input, .stTextArea textarea {
            background: #081423 !important;
            color: #e6edf7 !important;
            border: 1px solid rgba(105, 124, 170, 0.35) !important;
            border-radius: 12px !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #5577ff !important;
            box-shadow: 0 0 0 1px #5577ff !important;
        }

        [data-baseweb="select"] > div {
            background: #081423 !important;
            border: 1px solid rgba(105, 124, 170, 0.35) !important;
            border-radius: 12px !important;
            color: #e6edf7 !important;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #5577ff, #6c7cff) !important;
            color: white !important;
            border: 1px solid rgba(130, 150, 255, 0.5) !important;
            border-radius: 13px !important;
            font-weight: 800 !important;
            min-height: 42px;
        }

        div.stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(170, 185, 255, 0.8) !important;
        }

        div[data-testid="stRadio"] label {
            background: #0b1425;
            border: 1px solid rgba(105, 124, 170, 0.28);
            border-radius: 14px;
            padding: 0.5rem 0.75rem;
            margin-right: 0.5rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            border-bottom: 1px solid rgba(105, 124, 170, 0.24);
        }

        .stTabs [data-baseweb="tab"] {
            color: #9aa6bd !important;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            color: #e6edf7 !important;
            border-bottom: 2px solid #5577ff;
        }

        .dataframe {
            background: #091120 !important;
        }

        .stDataFrame {
            border: 1px solid rgba(105, 124, 170, 0.24);
            border-radius: 14px;
            overflow: hidden;
        }

        .small-pill {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: rgba(46, 233, 133, 0.12);
            border: 1px solid rgba(46, 233, 133, 0.25);
            color: #2ee985 !important;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .warn-pill {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: rgba(255, 176, 32, 0.12);
            border: 1px solid rgba(255, 176, 32, 0.28);
            color: #ffb020 !important;
            font-size: 0.8rem;
            font-weight: 700;
        }

        hr {
            border-color: rgba(105, 124, 170, 0.22);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def scorecard_to_dataframe(scorecard):
    rows = []
    for item in scorecard or []:
        rows.append(
            {
                "Category": item.category,
                "Score": f"{item.score}/{item.max_score}",
                "Evidence": item.evidence_level,
                "Rationale": item.rationale,
                "Diligence Question": item.diligence_question,
            }
        )
    return pd.DataFrame(rows)


def render_metric_cards(deal):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Overall Score</div>
              <div class="metric-value">{deal.opportunity_score} /100</div>
              <div class="metric-sub">Analysis complete</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Investment Fit</div>
              <div class="metric-value">{safe_text(deal.priority)}</div>
              <div class="metric-sub">Review diligence items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Deal Stage</div>
              <div class="metric-value">{safe_text(deal.stage)}</div>
              <div class="metric-sub">Based on notes</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Confidence</div>
              <div class="metric-value">{deal.confidence_score}</div>
              <div class="metric-sub">Evidence quality</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_results():
    col1, col2, col3, col4 = st.columns(4)

    empty_cards = [
        ("Overall Score", "— /100", "Paste notes first"),
        ("Investment Fit", "—", "Awaiting score"),
        ("Deal Stage", "—", "Awaiting analysis"),
        ("Confidence", "—", "Awaiting analysis"),
    ]

    for col, (label, value, sub) in zip([col1, col2, col3, col4], empty_cards):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value">{value}</div>
                  <div class="metric-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="panel">
          <div class="panel-title">Investment Thesis</div>
          <p class="muted">Paste company notes, click Analyze Deal, and the investment thesis will appear here.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_deal_result(deal):
    render_metric_cards(deal)

    tab_summary, tab_fields, tab_scorecard, tab_risks, tab_export = st.tabs(
        ["Executive Summary", "Structured Fields", "Diligence Scorecard", "Risks & Questions", "Export Preview"]
    )

    with tab_summary:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Investment Thesis")
        st.write(safe_text(deal.description))
        st.markdown("---")
        st.markdown("### Recommended Next Step")
        st.write(safe_text(deal.recommended_next_step))
        st.markdown("</div>", unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Key Upsides / Traction")
            if deal.traction_signals:
                for item in deal.traction_signals:
                    st.markdown(f"- {safe_text(item)}")
            else:
                st.write("No traction signals extracted.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Key Risks")
            if deal.risks:
                for item in deal.risks:
                    st.markdown(f"- {safe_text(item)}")
            else:
                st.write("No risks extracted.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_fields:
        field_rows = {
            "Company Name": deal.company_name,
            "Sector": deal.sector,
            "Subsector": deal.subsector,
            "Business Model": deal.business_model,
            "Stage": deal.stage,
            "Source Context": deal.relationship_context,
            "Priority": deal.priority,
            "Opportunity Score": deal.opportunity_score,
            "Confidence Score": deal.confidence_score,
            "CRM Tags": safe_text(deal.crm_tags),
        }
        st.dataframe(pd.DataFrame(field_rows.items(), columns=["Field", "Value"]), use_container_width=True)

    with tab_scorecard:
        df = scorecard_to_dataframe(deal.diligence_scorecard)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No scorecard generated.")

    with tab_risks:
        col_risk, col_questions = st.columns(2)

        with col_risk:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Risks")
            if deal.risks:
                for risk in deal.risks:
                    st.markdown(f"- {safe_text(risk)}")
            else:
                st.write("No risks extracted.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_questions:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Priority Diligence Questions")
            if deal.diligence_questions:
                for question in deal.diligence_questions:
                    st.markdown(f"- {safe_text(question)}")
            else:
                st.write("No diligence questions generated.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_export:
        preview_df = create_pipeline_dataframe([deal])
        st.dataframe(preview_df, use_container_width=True)
        csv = preview_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download This Deal CSV",
            data=csv,
            file_name=f"{deal.company_name.replace(' ', '_').lower()}_deal_record.csv",
            mime="text/csv",
        )


def clear_workspace():
    for key in [
        "company_name",
        "custom_notes",
        "investment_focus",
        "latest_deal",
    ]:
        if key in st.session_state:
            del st.session_state[key]


inject_css()

if "deals" not in st.session_state:
    st.session_state.deals = []

with st.sidebar:
    st.markdown(
        """
        <div class="brand-card">
          <div class="brand-title">💎 DealFlow AI</div>
          <div class="brand-sub">AI Deal Pipeline Assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Product Context")
    st.markdown(
        """
        <span class="muted">Workflow</span>

        1. Paste deal notes  
        2. Extract structured fields  
        3. Score opportunity  
        4. Generate diligence questions  
        5. Export CRM-ready data  
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    analysis_engine = st.selectbox(
        "Analysis Engine",
        ["Agents SDK v2", "OpenAI API v1"],
        index=0,
    )

    st.markdown("---")

    if st.button("Clear Workspace", use_container_width=True):
        clear_workspace()
        st.rerun()

    if st.button("Clear Pipeline", use_container_width=True):
        st.session_state.deals = []
        st.success("Pipeline cleared.")

    st.markdown("---")
    st.markdown(f"**Total Deals:** {len(st.session_state.deals)}")

    if st.session_state.deals:
        high_scores = [d for d in st.session_state.deals if d.opportunity_score >= 75]
        st.markdown(f"**High Score:** {len(high_scores)}")
    else:
        st.markdown("**High Score:** —")


st.markdown(
    """
    <div class="brand-card">
      <div class="brand-title">DealFlow AI — Analyst Workspace</div>
      <div class="brand-sub">Convert unstructured company notes into structured diligence, scoring, risks, and CRM-ready pipeline records.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

page_deal, page_pipeline, page_notes = st.tabs(
    ["Deal Intake", "Pipeline", "Evaluation Notes"]
)

with page_deal:
    left, right = st.columns([0.44, 0.56], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("## 1. Deal Intake")
        st.markdown('<p class="muted">Paste unstructured notes and provide basic context.</p>', unsafe_allow_html=True)

        mode = st.radio(
            "Analysis Mode",
            ["Sample Company Demo", "Custom Company Analysis"],
            horizontal=True,
            key="analysis_mode",
        )

        if mode == "Sample Company Demo":
            sample_choice = st.selectbox(
                "Sample Company",
                list(REAL_SAMPLE_DEALS.keys()),
                key="sample_choice",
            )
            company_name = sample_choice
            source_type = "Sample demo"
            investment_focus = "Demo analysis"
            raw_notes = st.text_area(
                "Paste Company Notes",
                value=REAL_SAMPLE_DEALS[sample_choice],
                height=330,
                key="sample_notes",
            )
        else:
            company_name = st.text_input(
                "Company Name",
                key="company_name",
                placeholder="Example: Corgi Insurance, Stripe, Rippling, Canva",
            )

            source_type = st.selectbox(
                "Source Type",
                [
                    "Research notes",
                    "Company website text",
                    "Funding announcement",
                    "Investor update",
                    "Founder call notes",
                    "Other",
                ],
                key="source_type",
            )

            investment_focus = st.text_input(
                "Optional Investment Focus",
                key="investment_focus",
                placeholder="e.g. InsurTech, B2B SaaS, AI workflow automation",
            )

            custom_notes = st.text_area(
                "Paste Company Notes",
                key="custom_notes",
                height=330,
                placeholder="Paste company description, traction, customers, funding context, risks, competitors, or investment rationale here.",
            )

            raw_notes = f"""
Company name: {company_name}
Source type: {source_type}
Investment focus: {investment_focus}

Company notes:
{custom_notes}
""".strip()

        analyze_clicked = st.button("Analyze Deal", use_container_width=True)

        if analyze_clicked:
            if len(raw_notes.strip()) < 100:
                st.warning("Please provide more company context before analyzing.")
            else:
                try:
                    with st.spinner("Analyzing deal notes and generating diligence record..."):
                        if analysis_engine == "Agents SDK v2":
                            deal = analyze_deal_with_agents(raw_notes)
                        else:
                            deal = analyze_deal_with_llm(raw_notes)

                    st.session_state.latest_deal = deal
                    st.session_state.deals.append(deal)
                    st.success("Analysis complete.")

                except Exception as exc:
                    st.error(f"Error analyzing deal: {exc}")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("## 2. Live Analysis & Results")
        st.markdown('<p class="muted">Real backend analysis and structured output based on your notes.</p>', unsafe_allow_html=True)

        latest_deal = st.session_state.get("latest_deal")
        if latest_deal is None:
            render_empty_results()
        else:
            render_deal_result(latest_deal)

with page_pipeline:
    st.markdown("## Pipeline")
    st.markdown('<p class="muted">Analyzed deals saved in this session and exportable as CRM-ready data.</p>', unsafe_allow_html=True)

    if st.session_state.deals:
        pipeline_df = create_pipeline_dataframe(st.session_state.deals)

        display_columns = [
            "company_name",
            "sector",
            "stage",
            "opportunity_score",
            "priority",
            "confidence_score",
            "recommended_next_step",
            "crm_tags",
        ]

        cols = [col for col in display_columns if col in pipeline_df.columns]
        st.dataframe(pipeline_df[cols], use_container_width=True)

        with st.expander("Full export preview"):
            st.dataframe(pipeline_df, use_container_width=True)

        csv = pipeline_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download CRM-Ready CSV",
            data=csv,
            file_name="dealflow_pipeline_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No analyzed companies yet. Go to Deal Intake, paste notes, and click Analyze Deal.")

with page_notes:
    st.markdown("## Evaluation / Product Notes")

    st.markdown(
        """
        <div class="panel">
        <h3>Current backend-connected capabilities</h3>

        <ul>
          <li>Runs real backend analysis through Agents SDK v2 or OpenAI API v1</li>
          <li>Produces a structured DealRecord</li>
          <li>Applies VC-style scoring and confidence scoring</li>
          <li>Saves analyzed deals into session pipeline</li>
          <li>Builds a CRM-ready pipeline table</li>
          <li>Exports pipeline data to CSV</li>
        </ul>

        <p class="muted">This version prioritizes working product behavior over the fragile iframe button bridge.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
