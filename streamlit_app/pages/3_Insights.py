"""Page 3: Proactive Insights Engine Results matching StitchMCP layout."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.insights.models import Severity
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

render_header("Proactive Empirical Insights", icon="💡")

if df is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# Insights Overview Stats Ribbon
crit_count = sum(1 for ins in insights if ins.severity in (Severity.CRITICAL, Severity.HIGH))
warn_count = sum(1 for ins in insights if ins.severity == Severity.MEDIUM)
info_count = sum(1 for ins in insights if ins.severity in (Severity.LOW, Severity.INFO))

st.markdown(
    f"""
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
        <div style="background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 1rem; font-family: var(--font-mono); font-size: 0.85rem;">
            Total Findings: <strong style="color: #4cd7f6;">{len(insights)}</strong>
        </div>
        <div style="background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 1rem; font-family: var(--font-mono); font-size: 0.85rem;">
            Critical / High: <strong style="color: {'#f43f5e' if crit_count > 0 else '#10b981'};">{crit_count}</strong>
        </div>
        <div style="background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 1rem; font-family: var(--font-mono); font-size: 0.85rem;">
            Medium / Warnings: <strong style="color: {'#fbbf24' if warn_count > 0 else '#e5e1e4'};">{warn_count}</strong>
        </div>
        <div style="background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 1rem; font-family: var(--font-mono); font-size: 0.85rem;">
            Informational: <strong style="color: #d0bcff;">{info_count}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search & Severity Filtering
col1, col2 = st.columns([3, 1])
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
    filtered_insights = [
        ins for ins in filtered_insights if ins.severity.value.upper() == selected_severity
    ]

if search_query:
    filtered_insights = [
        ins
        for ins in filtered_insights
        if search_query.lower() in ins.title.lower()
        or search_query.lower() in ins.category.value.lower()
    ]

render_insight_cards(filtered_insights)
render_footer()
