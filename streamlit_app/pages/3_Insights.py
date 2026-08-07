"""Page 3: Proactive Insights Engine Results."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.insight_card import render_insight_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Insights — {APP_TITLE}",
    page_icon="💡",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
insights = get_state("insights", [])

render_header("Proactive Data Insights", icon="💡")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# Search & Severity Filtering
col1, col2 = st.columns([2, 1])
with col1:
    search_query = st.text_input("🔍 Search Insights by title or category...", value="")
with col2:
    selected_severity = st.selectbox(
        "Filter by Severity",
        options=["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
        index=0,
    )

filtered_insights = insights
if selected_severity != "ALL":
    filtered_insights = [ins for ins in filtered_insights if ins.severity.value.upper() == selected_severity]

if search_query:
    filtered_insights = [
        ins
        for ins in filtered_insights
        if search_query.lower() in ins.title.lower() or search_query.lower() in ins.category.value.lower()
    ]

st.markdown("Deterministically evaluated rule findings backed by structured evidence.")
st.write("---")

render_insight_cards(filtered_insights)
render_footer()
