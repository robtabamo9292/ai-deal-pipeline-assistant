import streamlit as st


CSS = """
<style>
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"] {
  display: none !important;
}
.stApp { background: #F7F8FA; color: #172033; }
.block-container { max-width: 1480px; padding-top: 1.3rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E4E7EC; }
h1, h2, h3, h4, h5, h6, p, label, span, div { color: #172033; }
.muted { color: #667085 !important; font-size: .92rem; }
.sidebar-brand { border-bottom: 1px solid #E4E7EC; padding: .3rem 0 1rem; margin-bottom: 1rem; }
.sidebar-title { font-size: 1.12rem; font-weight: 700; letter-spacing: -.01em; }
.sidebar-sub { color: #667085; font-size: .82rem; margin-top: .15rem; }
.section-title { font-size: 1.25rem; font-weight: 700; letter-spacing: -.015em; margin-bottom: .2rem; }
.metric-card { background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 10px; padding: .95rem; min-height: 106px; }
.metric-label { color: #667085 !important; font-size: .76rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
.metric-value { font-size: 1.45rem; font-weight: 700; line-height: 1.2; margin-top: .4rem; font-variant-numeric: tabular-nums; }
.metric-sub { color: #667085 !important; font-size: .78rem; margin-top: .35rem; }
.status-strip { background: #F2F4F7; border: 1px solid #E4E7EC; border-radius: 8px; padding: .65rem .8rem; margin: .7rem 0 1rem; font-size: .82rem; color: #475467; }
.evidence-bar { height: 8px; background: #EAECF0; border-radius: 999px; overflow: hidden; margin-top: .5rem; }
.evidence-fill { height: 100%; background: #344054; border-radius: 999px; }
[data-baseweb="tab-list"] { gap: 1.2rem; border-bottom: 1px solid #E4E7EC; }
[data-baseweb="tab"] { color: #667085 !important; font-weight: 600; }
[aria-selected="true"] { color: #172033 !important; border-bottom: 2px solid #172033; }
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  background: #FFFFFF !important; border: 1px solid #D0D5DD !important; border-radius: 8px !important;
}
div.stButton > button, div.stDownloadButton > button {
  background: #172033 !important; color: #FFFFFF !important; border: 1px solid #172033 !important;
  border-radius: 8px !important; font-weight: 650 !important; min-height: 40px;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #344054 !important; }
[data-testid="stDataFrame"] { border: 1px solid #E4E7EC; border-radius: 8px; overflow: hidden; }
hr { border-color: #E4E7EC; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
