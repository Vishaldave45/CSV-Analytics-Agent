"""Sidebar navigation component matching StitchMCP / LOGIC_OS 2.0 design system."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import APP_SUBTITLE, APP_TITLE, APP_VERSION
from streamlit_app.services.session import get_state, set_state


def render_sidebar() -> None:
    """Render StitchMCP dark command center sidebar header, dataset status, insights, and footer."""
    with st.sidebar:
        header_html = f"""
        <div style="padding-bottom: 1rem; border-bottom: 1px solid #1e293b; margin-bottom: 1.25rem;">
            <div class="brand-title">{APP_TITLE}</div>
            <div class="brand-subtitle">{APP_SUBTITLE}</div>
            <div style="margin-top: 0.5rem;">
                <span class="brand-status-badge">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #4cd7f6;"></span>
                    CORE_V2 • OPERATIONAL
                </span>
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        dataset_name = get_state("dataset_name", "No dataset loaded")
        df = get_state("raw_df")
        insights = get_state("insights", [])
        active_filters = get_state("active_filters", [])

        st.markdown(
            '<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397; '
            'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem;">'
            "ACTIVE DATASET</div>",
            unsafe_allow_html=True,
        )
        
        st.markdown(
            f"""
            <div style="background: rgba(20, 20, 26, 0.85); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem;">
                <div style="font-family: var(--font-mono); font-weight: 700; color: #4cd7f6; font-size: 0.88rem; word-break: break-all;">
                    {dataset_name}
                </div>
                <div style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">
                    {f"{len(df):,} rows × {len(df.columns)} cols" if df is not None else "No data indexed"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Active Filters
        if active_filters:
            st.write("---")
            st.markdown(
                '<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397; '
                'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem;">'
                "ACTIVE CONSTRAINTS</div>",
                unsafe_allow_html=True,
            )
            for filt in active_filters:
                cols = ", ".join(filt.get("target_columns", []))
                st.markdown(
                    f"""
                    <div style="background: rgba(76, 215, 246, 0.08); border: 1px solid rgba(76, 215, 246, 0.3); border-radius: 6px; padding: 0.4rem 0.6rem; margin-bottom: 0.4rem; font-family: var(--font-mono); font-size: 0.75rem; color: #acedff;">
                        <code>{cols}</code>: {filt.get('parameters', '')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if st.button("Reset Constraints", key="btn_reset_filters_sidebar", use_container_width=True):
                set_state("active_filters", [])
                st.rerun()

        # Proactive Insights Sidebar List
        st.write("---")
        st.markdown(
            '<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397; '
            'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">'
            "PROACTIVE FINDINGS</div>",
            unsafe_allow_html=True,
        )

        if not insights and df is not None:
            st.markdown("_No data quality anomalies detected._")
        elif not insights:
            st.markdown("_Upload CSV to generate proactive findings._")
        else:
            for _idx, insight in enumerate(insights[:3]):
                category = insight.category.value.upper()
                badge_class = "badge-quality"
                glow_border = "#d0bcff"
                if "missing" in category.lower() or "duplicate" in category.lower():
                    badge_class = "badge-anomaly"
                    glow_border = "#fbbf24"
                elif "cardinality" in category.lower():
                    badge_class = "badge-trend"
                    glow_border = "#4cd7f6"

                card_html = f"""
                <div class="glass-panel" style="border-left: 3px solid {glow_border}; padding: 0.75rem; margin-bottom: 0.6rem;">
                    <span class="badge {badge_class}" style="font-size: 0.62rem; padding: 0.15rem 0.45rem;">{category}</span>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #e5e1e4; margin-top: 0.3rem;">
                        {insight.title}
                    </div>
                    <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 0.2rem; line-height: 1.4;">
                        {insight.description[:90]}...
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

        st.write("---")
        st.markdown(
            f'<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; text-align: center;">'
            f"LOGIC_OS {APP_VERSION}</div>",
            unsafe_allow_html=True,
        )


__all__ = ["render_sidebar"]
