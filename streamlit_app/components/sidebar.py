"""Sidebar navigation component for Quiet Data Studio."""

from __future__ import annotations

import streamlit as st

from streamlit_app.services.session import clear_dataset_session, get_state, set_state


def render_sidebar() -> None:
    """Render quiet data studio sidebar navigation."""
    with st.sidebar:
        # Header Brand
        header_html = """
        <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #334155; margin-bottom: 1rem;">
            <div class="studio-title" style="font-size: 1.4rem;">Data Studio</div>
            <div class="studio-subtitle">CSV Analytics & Exploration Workspace</div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        # Action: New Analysis
        if st.button("＋ New Analysis", key="btn_new_analysis_sidebar", use_container_width=True):
            set_state("messages", [])
            set_state("active_filters", [])
            set_state("pending_prompt", None)
            st.rerun()

        st.write("")

        # Section: Active Dataset
        dataset_name = get_state("dataset_name", "No dataset loaded")
        df = get_state("raw_df")
        insights = get_state("insights", [])

        st.markdown(
            '<div style="font-size: 0.74rem; font-weight: 600; color: #64748b; '
            'text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">'
            "DATASET INFO</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.65rem 0.85rem; margin-bottom: 0.85rem;">
                <div style="font-weight: 600; color: #38bdf8; font-size: 0.85rem; word-break: break-all;">
                    📄 {dataset_name}
                </div>
                <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem;">
                    {f"{len(df):,} rows × {len(df.columns)} cols" if df is not None else "No data loaded"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Section: Navigation Links
        st.markdown(
            '<div style="font-size: 0.74rem; font-weight: 600; color: #64748b; '
            'text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">'
            "EXPLORE</div>",
            unsafe_allow_html=True,
        )

        if st.button("💬  Chat Workspace", key="nav_chat", use_container_width=True):
            st.switch_page("pages/5_AI_Chat.py")
        if st.button("📊  Dataset Overview", key="nav_dataset", use_container_width=True):
            st.switch_page("pages/2_Dataset.py")
        if st.button("💡  Insights", key="nav_insights", use_container_width=True):
            st.switch_page("pages/3_Insights.py")
        if st.button("🎨  Visualizations", key="nav_visuals", use_container_width=True):
            st.switch_page("pages/4_Visualizations.py")
        if st.button("⚙️  Settings", key="nav_settings", use_container_width=True):
            st.switch_page("pages/7_Settings.py")

        # Proactive Findings Preview
        if insights:
            st.write("---")
            st.markdown(
                '<div style="font-size: 0.74rem; font-weight: 600; color: #64748b; '
                'text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">'
                "KEY INSIGHTS</div>",
                unsafe_allow_html=True,
            )
            for insight in insights[:2]:
                st.markdown(
                    f"""
                    <div style="background: #162032; border-left: 3px solid #38bdf8; border-radius: 6px; padding: 0.45rem 0.65rem; margin-bottom: 0.4rem; font-size: 0.78rem; color: #cbd5e1;">
                        <strong>{insight.title}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("---")

        # Clear Dataset Action
        if st.button("🗑️ Clear Dataset Session", key="nav_clear", use_container_width=True):
            clear_dataset_session()
            st.rerun()


__all__ = ["render_sidebar"]
