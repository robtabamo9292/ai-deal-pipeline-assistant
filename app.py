import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent_workflow import analyze_deal_with_agents
from src.llm import analyze_deal_with_llm
from src.export import create_pipeline_dataframe


load_dotenv()


st.set_page_config(
    page_title="DealFlow AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
            background: #060a16;
            color: #e8eefc;
        }

        .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            max-width: 1520px !important;
        }

        section[data-testid="stSidebar"] {
            background: #07101f;
            border-right: 1px solid rgba(105, 124, 170, 0.22);
        }

        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: #e8eefc;
        }

        .muted {
            color: #95a2ba !important;
            font-size: 0.94rem;
        }

        .sidebar-brand {
            background: linear-gradient(135deg, rgba(82, 111, 255, 0.18), rgba(10, 18, 35, 0.98));
            border: 1px solid rgba(100, 125, 255, 0.28);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .sidebar-title {
            font-size: 1.18rem;
            font-weight: 850;
            letter-spacing: -0.03em;
        }

        .sidebar-sub {
            color: #95a2ba;
            font-size: 0.82rem;
            margin-top: 0.15rem;
        }

        .section-card {
            background: #081423;
            border: 1px solid rgba(105, 124, 170, 0.25);
            border-radius: 18px;
            padding: 1.1rem 1.15rem;
            margin-bottom: 1rem;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.16);
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 850;
            letter-spacing: -0.035em;
            margin-bottom: 0.2rem;
        }

        .metric-card {
            background: #081423;
            border: 1px solid rgba(105, 124, 170, 0.25);
            border-radius: 16px;
            padding: 1rem;
            min-height: 112px;
        }

        .metric-label {
            color: #95a2ba !important;
            font-size: 0.82rem;
            margin-bottom: 0.55rem;
        }

        .metric-value {
            font-size: 1.55rem;
            font-weight: 850;
            letter-spacing: -0.04em;
            line-height: 1.12;
        }

        .metric-sub {
            color: #2ee985 !important;
            font-size: 0.8rem;
            margin-top: 0.45rem;
        }

        .small-label {
            color: #a7b3ca !important;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .stTextInput input, .stTextArea textarea {
            background: #071525 !important;
            color: #e8eefc !important;
            border: 1px solid rgba(105, 124, 170, 0.34) !important;
            border-radius: 13px !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #5577ff !important;
            box-shadow: 0 0 0 1px #5577ff !important;
        }

        [data-baseweb="select"] > div {
            background: #071525 !important;
            border: 1px solid rgba(105, 124, 170, 0.34) !important;
            border-radius: 13px !important;
            color: #e8eefc !important;
        }

        div.stButton > button, div.stDownloadButton > button {
            background: linear-gradient(135deg, #5577ff, #6c7cff) !important;
            color: white !important;
            border: 1px solid rgba(130, 150, 255, 0.5) !important;
            border-radius: 13px !important;
            font-weight: 800 !important;
            min-height: 42px;
        }

        div.stButton > button:hover, div.stDownloadButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(170, 185, 255, 0.85) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            border-bottom: 1px solid rgba(105, 124, 170, 0.24);
        }

        .stTabs [data-baseweb="tab"] {
            color: #9aa6bd !important;
            font-weight: 750;
        }

        .stTabs [aria-selected="true"] {
            color: #e8eefc !important;
            border-bottom: 2px solid #5577ff;
        }

        hr {
            border-color: rgba(105, 124, 170, 0.22);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_text(value, fallback="—"):
    if value is None:
        return fallback

    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip() and str(v).strip().lower() != "unknown"]
        return "; ".join(cleaned) if cleaned else fallback

    value = str(value).strip()
    if not value or value.lower() == "unknown":
        return fallback

    return value.replace("$", "\\$")


def clean_list(values):
    if not values:
        return []

    cleaned = []
    for value in values:
        value = str(value).strip()
        if value and value.lower() not in {"unknown", "none", "n/a", "not provided"}:
            cleaned.append(value)

    return cleaned


def limit_words(text, max_words=350):
    text = clean_text(text, "")
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip() + "..."


def fallback_risks(deal):
    risks = clean_list(deal.risks)
    if risks:
        return risks

    company = clean_text(deal.company_name, "The company")
    sector = clean_text(deal.sector, "").lower()

    inferred = [
        f"{company} has incomplete evidence on revenue quality, retention, and repeatable customer acquisition.",
        "Competitive positioning may be difficult to defend if incumbents or adjacent platforms can replicate the core workflow.",
        "Unit economics are not fully proven without clear gross margin, CAC, payback period, pricing, and expansion data.",
        "Growth may depend on continued access to reliable data, distribution, integrations, or partner channels.",
    ]

    if "data" in sector or "consumer" in sector:
        inferred.insert(1, "Consumer data, privacy, consent, and compliance expectations could create regulatory or trust-related risk.")

    if "health" in sector:
        inferred.insert(1, "Healthcare compliance, implementation complexity, and integration with existing clinical systems could slow adoption.")

    if "fintech" in sector or "finance" in sector:
        inferred.insert(1, "Financial services compliance, trust, and enterprise procurement requirements could lengthen sales cycles.")

    return inferred[:6]


def scorecard_dataframe(scorecard):
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


def render_metrics(deal):
    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("Overall Score", f"{deal.opportunity_score} /100", "Analysis complete"),
        ("Investment Fit", clean_text(deal.priority), "Review diligence"),
        ("Deal Stage", clean_text(deal.stage), "Based on notes"),
        ("Confidence", str(deal.confidence_score), "Evidence quality"),
    ]

    for col, (label, value, sub) in zip([c1, c2, c3, c4], cards):
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


def render_empty_results():
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("Overall Score", "— /100", "Paste notes first"),
        ("Investment Fit", "—", "Awaiting score"),
        ("Deal Stage", "—", "Awaiting analysis"),
        ("Confidence", "—", "Awaiting analysis"),
    ]

    for col, (label, value, sub) in zip([c1, c2, c3, c4], cards):
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
        <div class="section-card">
          <div class="section-title">Investment Thesis</div>
          <p class="muted">Paste company notes and click Analyze Deal to generate a thesis, risks, diligence questions, and CRM-ready pipeline record.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(deal):
    render_metrics(deal)

    tab_summary, tab_fields, tab_scorecard, tab_risks, tab_export = st.tabs(
        ["Executive Summary", "Structured Fields", "Diligence Scorecard", "Risks & Questions", "Export Preview"]
    )

    with tab_summary:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Investment Thesis")
        st.write(limit_words(deal.description, 350))
        st.markdown("---")
        st.markdown("### Recommended Next Step")
        st.write(clean_text(deal.recommended_next_step))
        st.markdown("</div>", unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Key Upsides / Traction")
            upsides = clean_list(deal.traction_signals)
            if upsides:
                for item in upsides:
                    st.markdown(f"- {clean_text(item)}")
            else:
                st.markdown("- Not enough traction evidence was provided.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Key Risks")
            for risk in fallback_risks(deal):
                st.markdown(f"- {clean_text(risk)}")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_fields:
        fields = {
            "Company Name": deal.company_name,
            "Sector": deal.sector,
            "Subsector": deal.subsector,
            "Business Model": deal.business_model,
            "Stage": deal.stage,
            "Priority": deal.priority,
            "Opportunity Score": deal.opportunity_score,
            "Confidence Score": deal.confidence_score,
            "Source Context": deal.relationship_context,
            "CRM Tags": clean_text(deal.crm_tags),
        }
        st.dataframe(pd.DataFrame(fields.items(), columns=["Field", "Value"]), use_container_width=True)

    with tab_scorecard:
        df = scorecard_dataframe(deal.diligence_scorecard)
        if df.empty:
            st.info("No scorecard generated.")
        else:
            st.dataframe(df, use_container_width=True)

    with tab_risks:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Investment Risks")
            for risk in fallback_risks(deal):
                st.markdown(f"- {clean_text(risk)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Diligence Questions")
            questions = clean_list(deal.diligence_questions)
            if questions:
                for q in questions:
                    st.markdown(f"- {clean_text(q)}")
            else:
                st.markdown("- What evidence supports revenue quality, retention, customer demand, and defensibility?")
                st.markdown("- What are the largest risks to adoption, margins, and competitive positioning?")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_export:
        preview = create_pipeline_dataframe([deal])
        st.dataframe(preview, use_container_width=True)
        st.download_button(
            "Download This Deal CSV",
            data=preview.to_csv(index=False).encode("utf-8"),
            file_name=f"{clean_text(deal.company_name, 'deal').replace(' ', '_').lower()}_deal_record.csv",
            mime="text/csv",
        )


def clear_workspace():
    st.session_state["company_name"] = ""
    st.session_state["source_type"] = "Research notes"
    st.session_state["investment_focus"] = ""
    st.session_state["company_notes"] = ""
    st.session_state["latest_deal"] = None
    st.session_state["analysis_complete"] = False


def clear_pipeline():
    st.session_state["deals"] = []
    clear_workspace()


def analyze_current_deal(company_name, source_type, investment_focus, company_notes):
    raw_notes = f"""
Company name: {company_name}
Source type: {source_type}
Investment focus: {investment_focus}

Company notes:
{company_notes}
""".strip()

    with st.spinner("Analyzing deal notes and generating diligence record..."):
        try:
            deal = analyze_deal_with_agents(raw_notes)
        except Exception:
            deal = analyze_deal_with_llm(raw_notes)

    st.session_state.latest_deal = deal
    st.session_state.deals.append(deal)
    st.session_state.analysis_complete = True


inject_css()

if "deals" not in st.session_state:
    st.session_state.deals = []

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-title">💎 DealFlow AI</div>
          <div class="sidebar-sub">AI Deal Pipeline Assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="small-label">Workflow</div>', unsafe_allow_html=True)
    st.markdown(
        """
        1. Paste company notes  
        2. Extract structured fields  
        3. Score opportunity  
        4. Generate diligence questions  
        5. Export CRM-ready data  
        """
    )

    st.markdown("---")

    st.markdown('<div class="small-label">Pipeline Quick View</div>', unsafe_allow_html=True)
    total = len(st.session_state.deals)
    high_score = len([d for d in st.session_state.deals if d.opportunity_score >= 75])
    st.markdown(f"**Total Deals:** {total}")
    st.markdown(f"**High Score:** {high_score if total else '—'}")

    st.markdown("---")

    st.button("Clear Workspace", use_container_width=True, on_click=clear_workspace)
    st.button("Clear Pipeline", use_container_width=True, on_click=clear_pipeline)


tab_deal, tab_pipeline = st.tabs(["Deal Intake", "Pipeline"])

with tab_deal:
    left, right = st.columns([0.42, 0.58], gap="large")

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Deal Intake</div>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Paste unstructured company notes and generate a structured diligence record.</p>', unsafe_allow_html=True)

        company_name = st.text_input(
            "Company Name",
            key="company_name",
            placeholder="Example: Pogo, Ramp, Rippling, Canva",
        )

        source_type = st.selectbox(
            "Source Type",
            ["Research notes", "Company website text", "Funding announcement", "Founder call notes", "Investor update", "Other"],
            key="source_type",
        )

        investment_focus = st.text_input(
            "Optional Investment Focus",
            key="investment_focus",
            placeholder="e.g. B2B SaaS, fintech infrastructure, healthcare workflow automation",
        )

        company_notes = st.text_area(
            "Paste Company Notes",
            key="company_notes",
            height=360,
            placeholder="Paste company description, traction, customers, business model, funding context, competitors, risks, or investment rationale.",
        )

        if st.button("Analyze Deal", use_container_width=True):
            if len(company_notes.strip()) < 100:
                st.warning("Please provide more company context before analyzing.")
            else:
                try:
                    analyze_current_deal(company_name, source_type, investment_focus, company_notes)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error analyzing deal: {exc}")

        if st.session_state.get("analysis_complete"):
            st.success("Analysis complete.")
            st.session_state.analysis_complete = False

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-title">2. Live Analysis & Results</div>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Backend-generated thesis, scoring, risks, diligence questions, and export-ready pipeline output.</p>', unsafe_allow_html=True)

        latest = st.session_state.get("latest_deal")
        if latest is None:
            render_empty_results()
        else:
            render_result(latest)

with tab_pipeline:
    st.markdown('<div class="section-title">Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<p class="muted">Analyzed deals saved in this session and exportable as CRM-ready data.</p>', unsafe_allow_html=True)

    if not st.session_state.deals:
        st.info("No analyzed companies yet. Go to Deal Intake, paste notes, and click Analyze Deal.")
    else:
        df = create_pipeline_dataframe(st.session_state.deals)

        display_cols = [
            "company_name",
            "sector",
            "stage",
            "opportunity_score",
            "priority",
            "confidence_score",
            "recommended_next_step",
            "risks",
            "diligence_questions",
        ]

        display_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)

        with st.expander("Full export preview"):
            st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download CRM-Ready CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="dealflow_pipeline_export.csv",
            mime="text/csv",
        )
