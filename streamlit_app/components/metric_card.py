"""Metric card component."""

from __future__ import annotations

import streamlit as st


def render_metric_card(label: str, value: str | int | float, subtext: str = "") -> None:
    """Render a stylized KPI metric card."""
    sub_html = (
        f'<div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">{subtext}</div>'
        if subtext
        else ""
    )
    card_html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


__all__ = ["render_metric_card"]
