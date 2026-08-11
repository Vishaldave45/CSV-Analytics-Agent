"""Evidence & Trust Attribution Component for Quiet Data Studio."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_evidence_drawer(
    metadata: dict[str, Any] | None = None,
    row_count: int | None = None,
    calculation_summary: str | None = None,
) -> None:
    """Render subtle Evidence & Trust attribution layer below assistant analysis responses.

    Args:
        metadata: Execution metadata dictionary.
        row_count: Optional integer number of rows analyzed in dataset context.
        calculation_summary: Optional plain-english logic explanation string.
    """
    if metadata is None:
        metadata = {}

    dev_mode = st.session_state.get("developer_mode", False)
    retrieved_cols = metadata.get("retrieved_columns") or []
    cols_str = ", ".join(retrieved_cols) if retrieved_cols else "All columns"
    rows_str = f"{row_count:,} rows" if row_count is not None else "Dataset scope"

    # Subtle Evidence Attribution Line
    st.markdown(
        f"""
        <div style="margin-top: 0.6rem; font-size: 0.78rem; color: #64748b; display: flex; align-items: center; gap: 0.75rem;">
            <span>Based on {rows_str}</span>
            <span>•</span>
            <span>Columns analyzed: <span style="color: #94a3b8;">{cols_str}</span></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    calc_text = calculation_summary or (f"Analyzed {rows_str} across {cols_str}.")

    with st.expander("How this was calculated", expanded=False):
        st.markdown(
            f"""
            <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
                <p style="margin: 0 0 0.4rem 0;">{calc_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if dev_mode:
            st.markdown(
                f"""
                <div style="background: #162032; border: 1px solid #334155; border-radius: 6px; padding: 0.75rem; margin-top: 0.5rem; font-family: var(--font-mono); font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.2rem 0; border-bottom: 1px dashed #243144;">
                        <span style="color: #64748b;">Tool:</span>
                        <span style="color: #38bdf8;">{metadata.get("tool_name", "analytics.query")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.2rem 0; border-bottom: 1px dashed #243144;">
                        <span style="color: #64748b;">Engine Provider:</span>
                        <span style="color: #38bdf8;">{metadata.get("engine_provider", "AnalyticsEngine")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.2rem 0;">
                        <span style="color: #64748b;">Thread ID:</span>
                        <span style="color: #38bdf8;">{metadata.get("thread_id", "default")}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
