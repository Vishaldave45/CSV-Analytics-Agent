"""CSV Analytics Agent — Streamlit Application Entry Point."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from csv_analytics_agent.logging_config import configure_logging
from csv_analytics_agent.observability.tracing import configure_langsmith
from streamlit_app.components.dataset_card import render_dataset_card
from streamlit_app.components.footer import render_footer
from streamlit_app.components.profile_card import render_profile_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.uploader import render_uploader
from streamlit_app.config import APP_ICON, APP_TITLE
from streamlit_app.services.session import get_state, init_session_state
from streamlit_app.theme import apply_custom_theme

# Load environment variables from .env
load_dotenv()

# Configure structured logging once at process start
configure_logging(level="INFO", json_output=False)

# Configure LangSmith tracing if enabled
configure_langsmith()

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{APP_TITLE} — Tabular Analytics Agent",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Custom Design System CSS
apply_custom_theme()

# Initialize Session State
init_session_state()

# Render Sidebar
render_sidebar()

# Main Content Router
df = get_state("raw_df")
profile = get_state("profile")

if df is None or profile is None:
    render_uploader()
else:
    dataset_name = get_state("dataset_name", "dataset.csv")
    render_dataset_card(profile, dataset_name=dataset_name)
    render_profile_cards(profile)

    st.write("")
    st.markdown(
        """
        <div class="glass-panel" style="padding: 1.25rem 1.5rem; margin-top: 0.5rem; margin-bottom: 1.5rem;">
            <h3 style="margin: 0 0 0.5rem 0; font-family: var(--font-display); color: #4cd7f6;">
                ⚡ Command Hub Navigation
            </h3>
            <p style="color: #cbd5e1; font-size: 0.92rem; margin: 0;">
                Your dataset has been parsed, profiled, and indexed into deterministic memory.
                Use the sidebar or quick actions below to explore:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🧬 Inspect Column DNA", use_container_width=True):
            st.switch_page("pages/2_Dataset.py")
    with c2:
        if st.button("💡 View Proactive Insights", use_container_width=True):
            st.switch_page("pages/3_Insights.py")
    with c3:
        if st.button("🤖 Launch AI Chat Agent", use_container_width=True):
            st.switch_page("pages/5_AI_Chat.py")

render_footer()
