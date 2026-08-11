"""Evidence & Trust Attribution Component for Stage 8.11 AI Analytics Workspace."""

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
        metadata: Execution metadata dictionary (router node, planner rule, engine provider, etc.).
        row_count: Optional integer number of rows analyzed in dataset context.
        calculation_summary: Optional plain-english logic explanation string.
    """
    if metadata is None:
        metadata = {}

    engine_provider = metadata.get("engine_provider", "AnalyticsEngine")
    tool_name = metadata.get("tool_name", "analytics.query")
    retrieved_cols = metadata.get("retrieved_columns") or []
    iterations = metadata.get("iteration_count", 1)

    cols_str = ", ".join(retrieved_cols) if retrieved_cols else "All Columns"
    rows_str = f"{row_count:,} rows" if row_count is not None else "Dataset scope"

    # Evidence Pill Footer
    st.markdown(
        f"""
        <div style="margin-top: 0.75rem; padding: 0.5rem 0.85rem; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 8px; font-family: var(--font-mono); font-size: 0.76rem; color: #94a3b8; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.85rem; flex-wrap: wrap;">
                <span>🛡️ <strong>EVIDENCE:</strong> Based on <strong>{rows_str}</strong></span>
                <span>• Columns: <code style="color: #4cd7f6;">{cols_str}</code></span>
                <span>• Engine: <span class="badge badge-optimal">{engine_provider}</span></span>
            </div>
            <div>
                <span style="color: #64748b;">Tool: {tool_name}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Expandable "View Calculation" Drawer
    calc_text = calculation_summary or (
        f"Query evaluated via **{engine_provider}** ({tool_name}) in {iterations} iteration(s). "
        f"Execution target columns: `{cols_str}`."
    )

    with st.expander("🔍 View Calculation & Execution Details", expanded=False):
        st.markdown(
            f"""
            <div style="font-family: var(--font-sans); font-size: 0.86rem; color: #cbd5e1; line-height: 1.5;">
                <p><strong>Methodology:</strong> {calc_text}</p>
                <div class="execution-details-card" style="margin-top: 0.5rem;">
                    <div class="execution-row">
                        <span class="execution-key">Planner Rule:</span>
                        <span class="execution-val">{metadata.get("planner_rule", "direct_query")}</span>
                    </div>
                    <div class="execution-row">
                        <span class="execution-key">Engine Provider:</span>
                        <span class="execution-val">{engine_provider}</span>
                    </div>
                    <div class="execution-row">
                        <span class="execution-key">Retrieved Columns:</span>
                        <span class="execution-val">{cols_str}</span>
                    </div>
                    <div class="execution-row">
                        <span class="execution-key">Session Thread:</span>
                        <span class="execution-val">{metadata.get("thread_id", "default_thread")}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
