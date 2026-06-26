from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="DealFlow AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu,
    footer,
    header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    .stApp {
        background: #0a0e1a;
    }

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    iframe {
        display: block;
        width: 100%;
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path("src/ui/analyst_workspace.html")

if not html_path.exists():
    st.error("Missing UI file: src/ui/analyst_workspace.html")
    st.stop()

html = html_path.read_text(encoding="utf-8")
components.html(html, height=1120, scrolling=True)
