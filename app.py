import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.llm import analyze_deal_with_llm
from src.export import create_pipeline_dataframe
from src.sample_data import REAL_SAMPLE_DEALS


load_dotenv()


def safe_markdown(text):
    return str(text).replace("$", "\\$")


def scorecard_to_dataframe(scorecard):
    rows = []

    for item in scorecard:
        rows.append(
            {
                "Category": item.category,
                "Score": f"{item.score}/{item.max_score}",
                "Evidence": item.evidence_level,
                "Rationale": item.rationale,
            }
        )

    return pd.DataFrame(rows)


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Main app background */
        .stApp {
            background-color: #0B1117;
            color: #F8FAFC;
        }

        /* Main content container */
        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        /* Hide Streamlit footer / menu / status widget */
        footer {
            visibility: hidden;
            height: 0%;
        }

        #MainMenu {
            visibility: hidden;
        }

        [data-testid="stStatusWidget"] {
            visibility: hidden;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #334155;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] li {
            color: #F8FAFC;
        }

        /* Headers */
        h1 {
            color: #F8FAFC;
            letter-spacing: -0.03em;
            font-weight: 800;
        }

        h2, h3 {
            color: #F8FAFC;
            letter-spacing: -0.02em;
        }

        /* Secondary text */
        .stCaption,
        caption,
        small {
            color: #CBD5E1 !important;
        }

        /* Dividers */
        hr {
            border: none;
            border-top: 1px solid #334155;
        }

        /* Main app buttons - Analyze Deal */
        div.stButton > button {
            background: linear-gradient(90deg, #3B82F6, #06B6D4) !important;
            color: #FFFFFF !important;
            border: 1px solid #3B82F6 !important;
            border-radius: 10px !important;
            padding: 0.55rem 1rem !important;
            font-weight: 700 !important;
            transition: 0.2s ease-in-out !important;
        }

        div.stButton > button:hover {
            background: linear-gradient(90deg, #2563EB, #0891B2) !important;
            border: 1px solid #60A5FA !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }

        /* Sidebar Clear Pipeline button */
        [data-testid="stSidebar"] div.stButton > button {
            background: transparent !important;
            color: #CBD5E1 !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transform: none !important;
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #1F2937 !important;
            color: #F8FAFC !important;
            border: 1px solid #64748B !important;
            transform: none !important;
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea {
            background-color: #111827 !important;
            color: #F8FAFC !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border: 1px solid #3B82F6 !important;
            box-shadow: 0 0 0 1px #3B82F6 !important;
        }

        /* Select boxes */
        [data-baseweb="select"] > div {
            background-color: #111827 !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            color: #F8FAFC !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            color: #CBD5E1 !important;
        }

        button[data-baseweb="tab"] p {
            color: #CBD5E1 !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #60A5FA !important;
            font-weight: 700 !important;
        }

        button[data-baseweb="tab"]:hover p {
            color: #93C5FD !important;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem;
        }

        [data-testid="stMetricLabel"] {
            color: #CBD5E1 !important;
        }

        [data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 800 !important;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid #334155;
        }

        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        [data-testid="stExpander"] details summary p {
            color: #F8FAFC !important;
            font-weight: 600;
        }

        /* Download button */
        div.stDownloadButton > button:first-child {
            background-color: #1F2937 !important;
            color: #F8FAFC !important;
            border: 1px solid #3B82F6 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }

        div.stDownloadButton > button:first-child:hover {
            background-color: #3B82F6 !important;
            color: #FFFFFF !important;
            border: 1px solid #60A5FA !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


st.set_page_config(
    page_title="DealFlow AI",
    page_icon="📊",
    layout="wide"
)

inject_custom_css()


if "deals" not in st.session_state:
    st.session_state.deals = []


st.title("DealFlow AI — AI Deal Pipeline Assistant")

st.caption(
    "Convert unstructured company, founder, and research notes into structured "
    "CRM-ready private markets opportunity records."
)


with st.sidebar:
    st.header("Product Context")

    st.markdown(
        """
        **Workflow:**  
        1. Paste deal notes  
        2. Extract structured fields  
        3. Score opportunity  
        4. Generate diligence questions  
        5. Export CRM-ready pipeline data  

        **Limitations:**  
        - Uses only the text provided  
        - Does not verify external facts  
        - Requires human review  
        - Not investment advice  
        """
    )

    st.markdown("---")

    if st.button("Clear Pipeline"):
        st.session_state.deals = []
        st.success("Pipeline cleared.")


tab1, tab2, tab3 = st.tabs(
    ["Deal Intake", "Pipeline Table", "Evaluation / Product Notes"]
)


with tab1:
    st.subheader("Deal Intake")

    input_mode = st.radio(
        "Choose analysis mode:",
        ["Sample Company Demo", "Custom Company Analysis"]
    )

    if input_mode == "Sample Company Demo":
        st.info(
            "Use this mode to test the product with built-in sample companies."
        )

        sample_choice = st.selectbox(
            "Choose a sample company:",
            list(REAL_SAMPLE_DEALS.keys())
        )

        raw_notes = st.text_area(
            "Sample company notes:",
            value=REAL_SAMPLE_DEALS[sample_choice],
            height=350
        )

    else:
        st.info(
            "Paste notes for any private company. For best results, include company description, "
            "business model, customers, traction, funding context, risks, and competitors."
        )

        custom_company_name = st.text_input(
            "Company name",
            placeholder="Example: Corgi Insurance, Stripe, Rippling, Canva"
        )

        source_type = st.selectbox(
            "Source type",
            [
                "Research notes",
                "Company website text",
                "Funding announcement",
                "Investor update",
                "Founder call notes",
                "Other"
            ]
        )

        investment_focus = st.text_input(
            "Optional investment focus",
            placeholder="Example: InsurTech, B2B SaaS, AI workflow automation, fintech infrastructure"
        )

        custom_notes = st.text_area(
            "Paste company notes:",
            height=350,
            placeholder=(
                "Paste company description, founder notes, funding context, traction, customers, "
                "risks, competitors, market notes, or investment rationale here."
            )
        )

        raw_notes = f"""
Company name: {custom_company_name}
Source type: {source_type}
Investment focus: {investment_focus}

Company notes:
{custom_notes}
"""

    analyze_button = st.button("Analyze Deal")

    if analyze_button:
        if len(raw_notes.strip()) < 100:
            st.warning(
                "Please provide more company context before analyzing. Include company description, "
                "business model, traction, customers, funding context, or risks."
            )
            st.stop()

        try:
            with st.spinner("Analyzing deal notes and generating diligence record..."):
                deal = analyze_deal_with_llm(raw_notes)
                st.session_state.deals.append(deal)

            st.success("Deal analyzed successfully.")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Opportunity Score", deal.opportunity_score)

            with col2:
                st.metric("Priority", deal.priority)

            with col3:
                st.metric("Confidence Score", deal.confidence_score)

            st.markdown("---")

            st.subheader("Due Diligence Scorecard")

            if deal.diligence_scorecard:
                scorecard_df = scorecard_to_dataframe(deal.diligence_scorecard)
                st.dataframe(scorecard_df)

                with st.expander("How this scorecard works"):
                    st.markdown(
                        """
                        The scorecard evaluates the company across diligence categories:
                        founder/team fit, market opportunity, product differentiation, traction/PMF,
                        customer clarity, business model, GTM scalability, competitive positioning,
                        and risk/compliance.

                        The opportunity score is calculated from the category scores. The confidence
                        score reflects how much supporting evidence appeared in the notes. Confidence
                        is capped when source links or citations are not provided.
                        """
                    )
            else:
                st.info("No scorecard generated.")

            st.markdown("---")

            st.subheader("Structured Deal Record")

            left, right = st.columns([0.60, 0.40])

            with left:
                st.markdown(f"### {safe_markdown(deal.company_name)}")
                st.markdown(f"**Sector:** {safe_markdown(deal.sector)}")
                st.markdown(f"**Subsector:** {safe_markdown(deal.subsector)}")
                st.markdown(f"**Business Model:** {safe_markdown(deal.business_model)}")
                st.markdown(f"**Stage:** {safe_markdown(deal.stage)}")
                st.markdown(f"**Description:** {safe_markdown(deal.description)}")
                st.markdown(f"**Source Context:** {safe_markdown(deal.relationship_context)}")
                st.markdown(f"**Recommended Next Step:** {safe_markdown(deal.recommended_next_step)}")

            with right:
                st.markdown("### CRM Tags")
                if deal.crm_tags:
                    for tag in deal.crm_tags:
                        st.markdown(f"- {safe_markdown(tag)}")
                else:
                    st.write("No CRM tags extracted.")

            st.markdown("---")

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown("### Traction Signals")
                if deal.traction_signals:
                    for item in deal.traction_signals:
                        st.markdown(f"- {safe_markdown(item)}")
                else:
                    st.write("No traction signals found.")

            with col_b:
                st.markdown("### Customer Segments")
                if deal.customer_signals:
                    for item in deal.customer_signals:
                        st.markdown(f"- {safe_markdown(item)}")
                else:
                    st.write("No customer segments found.")

            with col_c:
                st.markdown("### Funding Signals")
                if deal.funding_signals:
                    for item in deal.funding_signals:
                        st.markdown(f"- {safe_markdown(item)}")
                else:
                    st.write("No funding signals found.")

            st.markdown("---")

            col_risks, col_questions = st.columns(2)

            with col_risks:
                st.markdown("### Risks")
                if deal.risks:
                    for risk in deal.risks:
                        st.markdown(f"- {safe_markdown(risk)}")
                else:
                    st.write("No risks extracted.")

            with col_questions:
                st.markdown("### Priority Diligence Questions")
                if deal.diligence_questions:
                    for question in deal.diligence_questions:
                        st.markdown(f"- {safe_markdown(question)}")
                else:
                    st.write("No diligence questions generated.")

        except Exception as e:
            st.error(f"Error analyzing deal: {e}")


with tab2:
    st.subheader("CRM-Ready Pipeline Table")

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

        st.dataframe(pipeline_df[display_columns])

        with st.expander("Full export preview"):
            st.dataframe(pipeline_df)

        csv = pipeline_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CRM-Ready CSV",
            data=csv,
            file_name="deal_pipeline_export.csv",
            mime="text/csv"
        )

    else:
        st.info("No deals analyzed yet. Go to the Deal Intake tab and analyze a deal.")


with tab3:
    st.subheader("Evaluation / Product Notes")

    st.markdown(
        """
        This prototype demonstrates AI product-building around private markets and diligence workflows.

        ### What the app demonstrates

        - Converts unstructured deal notes into structured CRM-ready records
        - Extracts company profile, sector, business model, stage, traction, risks, and next steps
        - Generates diligence questions
        - Adds a due diligence scorecard across founder/team, market, product, traction, customer, business model, GTM, competition, and risk categories
        - Produces a downloadable CSV that could be imported into a CRM or Airtable-style workflow

        ### Due diligence scorecard categories

        - Founder / Team Fit
        - Market Opportunity
        - Product / Differentiation
        - Traction / PMF Evidence
        - Customer / ICP Clarity
        - Business Model / Unit Economics
        - GTM Scalability
        - Competitive Positioning
        - Risk / Legal / Compliance

        ### Quality guardrails

        - The model is instructed not to invent unsupported facts
        - Missing information should be marked as `Unknown`
        - Output includes a confidence score
        - Confidence is capped when source links or citations are not provided
        - Final investment decisions require human review
        - Sample data is based on public company information for demonstration purposes

        ### Why this matters

        Private markets teams often receive valuable information through emails, calls, websites, referrals, and research notes.  
        This tool shows how AI can standardize that information into structured workflow data that supports sourcing, diligence, prioritization, and relationship management.
        """
    )