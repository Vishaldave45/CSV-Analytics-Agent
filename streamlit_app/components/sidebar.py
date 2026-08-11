"""Sidebar navigation component for Stage 8.11 AI Analytics Workspace."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import APP_SUBTITLE, APP_TITLE, APP_VERSION
from streamlit_app.services.session import clear_dataset_session, get_state, set_state


def render_sidebar() -> None:
    """Render 4-section workspace sidebar navigation header, dataset pill, insights, and footer."""
    with st.sidebar:
        # Header Brand
        header_html = f"""
        <div style="padding-bottom: 0.85rem; border-bottom: 1px solid #1e293b; margin-bottom: 1rem;">
            <div class="brand-title" style="font-size: 1.6rem;">{APP_TITLE}</div>
            <div class="brand-subtitle">{APP_SUBTITLE}</div>
            <div style="margin-top: 0.4rem;">
                <span class="brand-status-badge">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #4cd7f6;"></span>
                    READY • LOGIC_OS v{APP_VERSION}
                </span>
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        # Section 1: Workspace Actions
        st.markdown(
            '<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; '
            'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;">'
            "WORKSPACE</div>",
            unsafe_allow_html=True,
        )

        if st.button("➕ New Analysis", key="btn_new_analysis_sidebar", use_container_width=True):
            set_state("messages", [])
            set_state("active_filters", [])
            set_state("pending_prompt", None)
            st.rerun()

        st.write("")

        # Section 2: Active Dataset Pill
        dataset_name = get_state("dataset_name", "No dataset loaded")
        df = get_state("raw_df")
        insights = get_state("insights", [])

        st.markdown(
            '<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; '
            'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;">'
            "ACTIVE DATASET</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background: rgba(20, 20, 26, 0.85); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.75rem;">
                <div style="font-family: var(--font-mono); font-weight: 700; color: #4cd7f6; font-size: 0.85rem; word-break: break-all;">
                    📄 {dataset_name}
                </div>
                <div style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">
                    {f"{len(df):,} rows × {len(df.columns)} cols" if df is not None else "No data loaded"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Section 3: Navigation Links
        st.markdown(
            '<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; '
            'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;">'
            "EXPLORE</div>",
            unsafe_allow_html=True,
        )

        c_nav1, c_nav2 = st.columns(2)
        with c_nav1:
            if st.button("🤖 Chat", key="nav_chat", use_container_width=True):
                st.switch_page("pages/5_AI_Chat.py")
        with c_nav2:
            if st.button("🧬 Dataset", key="nav_dataset", use_container_width=True):
                st.switch_page("pages/2_Dataset.py")

        c_nav3, c_nav4 = st.columns(2)
        with c_nav3:
            if st.button("💡 Insights", key="nav_insights", use_container_width=True):
                st.switch_page("pages/3_Insights.py")
        with c_nav4:
            if st.button("🎨 Visuals", key="nav_visuals", use_container_width=True):
                st.switch_page("pages/4_Visualizations.py")

        # Proactive Findings Preview
        if insights:
            st.write("---")
            st.markdown(
                '<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; '
                'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">'
                "EMPIRICAL FINDINGS</div>",
                unsafe_allow_html=True,
            )
            for insight in insights[:2]:
                st.markdown(
                    f"""
                    <div style="background: rgba(26, 26, 36, 0.6); border-left: 3px solid #4cd7f6; border-radius: 6px; padding: 0.45rem 0.65rem; margin-bottom: 0.4rem; font-size: 0.78rem; color: #cbd5e1;">
                        <strong>{insight.title}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("---")

        # Section 4: Settings & Reset
        c_set1, c_set2 = st.columns(2)
        with c_set1:
            if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
                st.switch_page("pages/7_Settings.py")
        with c_set2:
            if st.button("🧹 Clear", key="nav_clear", use_container_width=True):
                clear_dataset_session()
                st.rerun()


__all__ = ["render_sidebar"]
