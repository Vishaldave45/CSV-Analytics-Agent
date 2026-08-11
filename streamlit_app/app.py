"""CSV Analytics Agent — Streamlit AI Analytics Workspace Application Entry Point."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from csv_analytics_agent.logging_config import configure_logging
from csv_analytics_agent.observability.tracing import configure_langsmith
from streamlit_app.components.dataset_card import render_dataset_card
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.profile_card import render_profile_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.suggested_questions import render_initial_suggestions
from streamlit_app.components.uploader import render_uploader
from streamlit_app.config import APP_ICON, APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

# Load environment variables
load_dotenv()

# Configure logging & tracing
configure_logging(level="INFO", json_output=False)
configure_langsmith()

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{APP_TITLE} — AI Analytics Workspace",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Custom Theme CSS
apply_custom_theme()

# Render Sidebar
render_sidebar()

# Main Workspace Content Router
df = get_state("raw_df")
profile = get_state("profile")

if df is None or profile is None:
    render_uploader()
    render_initial_suggestions()
else:
    render_header("AI Analytics Workspace", icon="📊")
    dataset_name = get_state("dataset_name", "dataset.csv")
    render_dataset_card(profile, dataset_name=dataset_name)
    render_profile_cards(profile)

    st.write("")
    st.markdown(
        """
        <div class="glass-panel" style="padding: 1.25rem 1.5rem; margin-top: 0.5rem; margin-bottom: 1.25rem;">
            <h3 style="margin: 0 0 0.5rem 0; font-family: var(--font-display); color: #4cd7f6; font-size: 1.3rem;">
                ⚡ Workspace Navigation
            </h3>
            <p style="color: #cbd5e1; font-size: 0.92rem; margin: 0;">
                Your dataset is parsed and indexed into deterministic memory. Use the workspace pages below:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🤖 AI Chat Agent", key="btn_workspace_chat", use_container_width=True):
            st.switch_page("pages/5_AI_Chat.py")
    with c2:
        if st.button("🧬 Dataset DNA", key="btn_workspace_dataset", use_container_width=True):
            st.switch_page("pages/2_Dataset.py")
    with c3:
        if st.button(
            "💡 Empirical Insights", key="btn_workspace_insights", use_container_width=True
        ):
            st.switch_page("pages/3_Insights.py")
    with c4:
        if st.button("🎨 Visualizations", key="btn_workspace_visuals", use_container_width=True):
            st.switch_page("pages/4_Visualizations.py")

    render_initial_suggestions(
        on_select=lambda q: (
            st.session_state.update({"pending_prompt": q}),
            st.switch_page("pages/5_AI_Chat.py"),
        )
    )

render_footer()
