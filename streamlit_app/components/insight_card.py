"""Data quality and proactive insights component matching StitchMCP Evidence Cards."""

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
            <div class="glass-panel" style="text-align: center; padding: 2rem;">
                <div style="font-size: 1.8rem; color: #10b981; margin-bottom: 0.5rem;">✅</div>
                <h3 style="margin: 0; color: #e5e1e4;">Zero Structural Anomalies</h3>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.3rem;">
                    All deterministic validation and data quality rules passed successfully.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for idx, insight in enumerate(insights):
        # Determine semantic styling
        if insight.severity in (Severity.HIGH, Severity.CRITICAL):
            border_color = "#f43f5e"
            badge_cls = "badge-critical"
            icon_char = "⚡"
        elif insight.severity == Severity.MEDIUM:
            border_color = "#fbbf24"
            badge_cls = "badge-anomaly"
            icon_char = "⚠️"
        elif (
            "trend" in insight.category.value.lower()
            or "correlation" in insight.category.value.lower()
        ):
            border_color = "#4cd7f6"
            badge_cls = "badge-trend"
            icon_char = "📈"
        else:
            border_color = "#d0bcff"
            badge_cls = "badge-quality"
            icon_char = "🔍"

        badge_txt = (
            f"{icon_char} {insight.category.value.upper()} • {insight.severity.value.upper()}"
        )

        card_html = f"""
        <div class="glass-panel" style="border-left: 4px solid {border_color}; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                <span class="badge {badge_cls}">{badge_txt}</span>
                <span style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397;">
                    RULE ID #{idx + 1:02d}
                </span>
            </div>
            <h3 style="margin: 0.3rem 0 0.4rem 0; font-family: var(--font-display); font-size: 1.15rem; color: #e5e1e4;">
                {insight.title}
            </h3>
            <p style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.5; margin: 0;">
                {insight.description}
            </p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        exp_label = f"🔬 Empirical Evidence Facts ({len(insight.evidence)} items)"
        with st.expander(exp_label, expanded=False):
            for ev in insight.evidence:
                st.markdown(
                    f"- <code>{ev.metric}</code> = **`{ev.value}`** &nbsp;·&nbsp; Target: <code>{ev.column or 'Dataset'}</code>",
                    unsafe_allow_html=True,
                )
            if insight.recommendation:
                st.markdown(
                    f"""
                    <div style="margin-top: 0.6rem; padding: 0.6rem 0.8rem; background: rgba(76, 215, 246, 0.08); border-left: 2px solid #4cd7f6; border-radius: 4px; font-size: 0.85rem; color: #e5e1e4;">
                        💡 <strong>Actionable Guidance:</strong> {insight.recommendation}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


__all__ = ["render_insight_cards"]
