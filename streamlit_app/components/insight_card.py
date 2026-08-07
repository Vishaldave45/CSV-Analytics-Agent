"""Data quality insights component."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.insights.models import Insight, Severity


def render_insight_cards(insights: list[Insight]) -> None:
    """Render structured Insight cards backed by empirical evidence.

    Args:
        insights: List of Insight objects.
    """
    if not insights:
        st.success("No data quality warnings or anomalies detected in dataset.")
        return

    for insight in insights:
        sev_color = "#3b82f6"
        badge_cls = "badge-trend"
        if insight.severity in (Severity.HIGH, Severity.CRITICAL):
            sev_color = "#f43f5e"
            badge_cls = "badge-anomaly"
        elif insight.severity == Severity.MEDIUM:
            sev_color = "#f59e0b"
            badge_cls = "badge-quality"

        badge_txt = f"{insight.category.value} • {insight.severity.value}"
        card_html = (
            f'<div class="logic-card" style="border-left: 4px solid {sev_color};">'
            f'<span class="badge {badge_cls}">{badge_txt}</span>'
            f'<h4 style="margin: 0.3rem 0; color: #f8fafc;">{insight.title}</h4>'
            f'<p style="color: #cbd5e1; font-size: 0.9rem;">{insight.description}</p>'
            "</div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)

        exp_label = f"Empirical Evidence for '{insight.title}' ({len(insight.evidence)} facts)"
        with st.expander(exp_label):
            for ev in insight.evidence:
                st.markdown(f"- **{ev.metric}**: `{ev.value}` (Column: `{ev.column or 'Dataset'}`)")
            if insight.recommendation:
                st.info(f"💡 **Recommendation**: {insight.recommendation}")


__all__ = ["render_insight_cards"]
