"""Data quality and proactive insights component for Quiet Data Studio."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.insights.models import Insight, Severity


def render_insight_cards(insights: list[Insight]) -> None:
    """Render structured Insight cards backed by empirical evidence facts.

    Args:
        insights: List of Insight objects.
    """
    if not insights:
        st.markdown(
            """
            <div class="studio-card" style="text-align: center; padding: 2rem;">
                <h3 style="margin: 0; color: #f8fafc;">Zero Structural Anomalies</h3>
                <p style="color: #94a3b8; font-size: 0.88rem; margin-top: 0.3rem;">
                    All data quality and validation rules passed.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for idx, insight in enumerate(insights):
        badge_cls = "studio-badge-info"
        if insight.severity in (Severity.HIGH, Severity.CRITICAL):
            badge_cls = "studio-badge-warning"

        badge_txt = f"{insight.category.value.upper()} • {insight.severity.value.upper()}"

        card_html = f"""
        <div class="studio-card" style="margin-bottom: 0.85rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
                <span class="studio-badge {badge_cls}">{badge_txt}</span>
                <span style="font-size: 0.74rem; color: #64748b;">Finding #{idx + 1:02d}</span>
            </div>
            <h4 style="margin: 0.3rem 0 0.35rem 0; font-size: 1.05rem; color: #f8fafc;">
                {insight.title}
            </h4>
            <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                {insight.description}
            </p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        exp_label = f"Evidence ({len(insight.evidence)} facts)"
        with st.expander(exp_label, expanded=False):
            for ev in insight.evidence:
                st.markdown(
                    f"- Metric `{ev.metric}` = **`{ev.value}`** (Column: `{ev.column or 'Dataset'}`)"
                )
            if insight.recommendation:
                st.markdown(
                    f"""
                    <div style="margin-top: 0.5rem; padding: 0.5rem 0.75rem; background: #162032; border-left: 2px solid #38bdf8; border-radius: 4px; font-size: 0.85rem; color: #cbd5e1;">
                        <strong>Recommendation:</strong> {insight.recommendation}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


__all__ = ["render_insight_cards"]
