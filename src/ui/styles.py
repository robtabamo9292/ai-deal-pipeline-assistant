import streamlit as st


CSS = """
<style>
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
}

.stApp {
  background: #060A16;
  color: #E8EEFC;
}

.block-container {
  max-width: 1520px;
  padding-top: 1.25rem;
  padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
  background: #07101F;
  border-right: 1px solid rgba(105, 124, 170, 0.22);
}

h1, h2, h3, h4, h5, h6, p, label,
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMarkdownContainer"] {
  color: #E8EEFC;
}

[data-testid="stCaptionContainer"] p,
.stCaptionContainer,
.muted {
  color: #95A2BA !important;
}

.sidebar-brand {
  background: linear-gradient(135deg, rgba(82, 111, 255, 0.18), rgba(10, 18, 35, 0.98));
  border: 1px solid rgba(100, 125, 255, 0.28);
  border-radius: 18px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.sidebar-title {
  color: #E8EEFC !important;
  font-size: 1.18rem;
  font-weight: 850;
  letter-spacing: -0.03em;
}

.sidebar-sub {
  color: #95A2BA !important;
  font-size: 0.82rem;
  margin-top: 0.15rem;
}

.section-title {
  color: #E8EEFC !important;
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
  color: #95A2BA !important;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.metric-value {
  color: #E8EEFC !important;
  font-size: 1.55rem;
  font-weight: 850;
  letter-spacing: -0.04em;
  line-height: 1.12;
  margin-top: 0.45rem;
  font-variant-numeric: tabular-nums;
}

.metric-sub {
  color: #A7B3CA !important;
  font-size: 0.8rem;
  margin-top: 0.45rem;
}

.status-strip {
  background: #081423;
  border: 1px solid rgba(105, 124, 170, 0.25);
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
  margin: 0.7rem 0 1rem;
  color: #A7B3CA !important;
}

.evidence-bar {
  height: 8px;
  background: #142238;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.evidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #5577FF, #6C7CFF);
  border-radius: 999px;
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {
  background: #071525 !important;
  color: #E8EEFC !important;
  border: 1px solid rgba(105, 124, 170, 0.34) !important;
  border-radius: 13px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
  border-color: #5577FF !important;
  box-shadow: 0 0 0 1px #5577FF !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
  color: #73809A !important;
  opacity: 1 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] svg {
  color: #E8EEFC !important;
  fill: #E8EEFC !important;
}

.stButton button,
.stDownloadButton button,
[data-testid="stFormSubmitButton"] button {
  background: linear-gradient(135deg, #5577FF, #6C7CFF) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(130, 150, 255, 0.5) !important;
  border-radius: 13px !important;
  font-weight: 800 !important;
  min-height: 42px;
}

.stButton button *,
.stDownloadButton button *,
[data-testid="stFormSubmitButton"] button * {
  color: #FFFFFF !important;
}

.stButton button:hover,
.stDownloadButton button:hover,
[data-testid="stFormSubmitButton"] button:hover {
  transform: translateY(-1px);
  border-color: rgba(170, 185, 255, 0.85) !important;
}

.stButton button:disabled,
.stButton button[disabled],
.stButton button[aria-disabled="true"],
.stDownloadButton button:disabled,
.stDownloadButton button[disabled],
.stDownloadButton button[aria-disabled="true"] {
  background: #101A2C !important;
  border-color: rgba(105, 124, 170, 0.24) !important;
  opacity: 1 !important;
}

.stButton button:disabled *,
.stButton button[disabled] *,
.stButton button[aria-disabled="true"] *,
.stDownloadButton button:disabled *,
.stDownloadButton button[disabled] *,
.stDownloadButton button[aria-disabled="true"] * {
  color: #73809A !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 1rem;
  border-bottom: 1px solid rgba(105, 124, 170, 0.24);
}

.stTabs [data-baseweb="tab"] {
  color: #9AA6BD !important;
  font-weight: 750;
}

.stTabs [aria-selected="true"] {
  color: #E8EEFC !important;
  border-bottom: 2px solid #5577FF;
}

[data-testid="stAlert"] {
  background: #0B1B31 !important;
  border: 1px solid rgba(85, 119, 255, 0.3) !important;
  color: #DCE6FA !important;
}

[data-testid="stAlert"] * {
  color: #DCE6FA !important;
}

[data-testid="stExpander"] {
  background: #081423;
  border: 1px solid rgba(105, 124, 170, 0.25);
  border-radius: 13px;
}

[data-testid="stDataFrame"] {
  border: 1px solid rgba(105, 124, 170, 0.25);
  border-radius: 12px;
  overflow: hidden;
}

hr {
  border-color: rgba(105, 124, 170, 0.22);
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
