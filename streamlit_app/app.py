"""LOGIC_OS_2.0 Main Entrypoint Application."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.uploader import render_uploader
from streamlit_app.services.session import get_state, init_session_state

# 1. Configure Streamlit Page
st.set_page_config(
    page_title="LOGIC_OS_2.0 — AI CSV Analytics Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Custom LOGIC_OS_2.0 CSS Stylesheet
styles_path = Path(__file__).parent / "assets" / "styles.css"
if styles_path.exists():
    with open(styles_path, encoding="utf-8") as f:
        css_content = f.read()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# 3. Initialize Session State
init_session_state()

# 4. Render Sidebar
render_sidebar()

# 5. Render Main Content Router
df = get_state("raw_df")

if df is None:
    render_uploader()
else:
    dataset_name = get_state("dataset_name", "dataset.csv")
    insights = get_state("insights", [])

    header_html = (
        '<div class="logic-card logic-card-glowing" style="display: flex; '
        'justify-content: space-between; align-items: center;">'
        '<div><span class="badge badge-trend">ACTIVE DATASET</span>'
        f'<h2 style="margin: 0.2rem 0; color: #f8fafc;">{dataset_name}</h2>'
        f'<div style="font-size: 0.9rem; color: #94a3b8;">{len(df):,} rows × '
        f"{len(df.columns)} columns • {len(insights)} quality insights</div>"
        "</div></div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    st.info(
        "💡 Use the sidebar navigation menu on the left to switch between "
        "**Upload**, **Dataset Overview**, **Insights**, **Visualizations**, "
        "**AI Chat**, **History**, and **Settings**."
    )
