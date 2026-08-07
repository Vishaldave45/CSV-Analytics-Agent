"""Sidebar navigation component matching LOGIC_OS_2.0 design system."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import APP_SUBTITLE, APP_TITLE, APP_VERSION
from streamlit_app.services.session import get_state, set_state


def render_sidebar() -> None:
    """Render LOGIC_OS_2.0 dark sidebar header, dataset status, proactive insights, and footer."""
    with st.sidebar:
        header_html = (
            '<div style="padding-bottom: 1rem; border-bottom: 1px solid #1e293b; '
            'margin-bottom: 1.2rem;">'
            f'<div class="brand-title">{APP_TITLE}</div>'
            f'<div class="brand-subtitle">{APP_SUBTITLE}</div></div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)

        dataset_name = get_state("dataset_name", "No dataset loaded")
        df = get_state("raw_df")
        insights = get_state("insights", [])
        active_filters = get_state("active_filters", [])

        st.caption("ACTIVE DATASET")
        st.markdown(f"**`{dataset_name}`**")

        if df is not None:
            st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
        else:
            st.info("Upload a CSV file to begin analysis.")

        # Active Filters
        if active_filters:
            st.write("---")
            st.caption("ACTIVE FILTERS")
            for filt in active_filters:
                cols = ", ".join(filt.get("target_columns", []))
                st.markdown(f"`{cols}`: {filt.get('parameters', '')}")
            if st.button("Reset Filters", key="btn_reset_filters_sidebar"):
                set_state("active_filters", [])
                st.rerun()

        # Proactive Insights Sidebar List
        st.write("---")
        st.caption("PROACTIVE INSIGHTS")

        if not insights and df is not None:
            st.markdown("_No data quality anomalies detected._")
        elif not insights:
            st.markdown("_Upload CSV to generate proactive insights._")
        else:
            for _idx, insight in enumerate(insights[:3]):
                category = insight.category.value.upper()
                badge_class = "badge-quality"
                if "missing" in category.lower() or "duplicate" in category.lower():
                    badge_class = "badge-anomaly"
                elif "cardinality" in category.lower():
                    badge_class = "badge-trend"

                title_div = (
                    '<div style="font-size: 0.85rem; font-weight: 600; '
                    f'color: #f8fafc; margin-top: 0.2rem;">{insight.title}</div>'
                )
                card_html = (
                    '<div class="logic-card" style="padding: 0.8rem; margin-bottom: 0.6rem;">'
                    f'<span class="badge {badge_class}">{category}</span>'
                    f"{title_div}"
                    f'<div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">'
                    f"{insight.description}</div></div>"
                )
                st.markdown(card_html, unsafe_allow_html=True)

        st.write("---")
        st.caption(f"LOGIC_OS {APP_VERSION}")


__all__ = ["render_sidebar"]
