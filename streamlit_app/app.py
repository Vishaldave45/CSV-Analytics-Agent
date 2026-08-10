"""LOGIC_OS_2.0 Main Entrypoint Application."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.logging_config import configure_logging
from streamlit_app.components.dataset_card import render_dataset_card
from streamlit_app.components.footer import render_footer
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.uploader import render_uploader
from streamlit_app.config import APP_ICON, APP_TITLE
from streamlit_app.services.session import get_state, init_session_state
from streamlit_app.theme import apply_custom_theme

# Configure structured logging once at process start — must come before
# st.set_page_config so any import-time logging is captured.
configure_logging(level="INFO", json_output=False)

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{APP_TITLE} — AI CSV Analytics Agent",
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

    st.info(
        "💡 Use the sidebar navigation menu on the left to switch between "
        "**Upload**, **Dataset Overview**, **Insights**, **Visualizations**, "
        "**AI Chat**, **History**, and **Settings**."
    )

render_footer()
