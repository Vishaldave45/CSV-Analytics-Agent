"""Execution Trace component displaying metadata and pipeline steps matching StitchMCP."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_execution_trace(metadata: dict[str, Any] | None = None) -> None:
    """Render collapsible Execution Details panel matching Stitch design deliverable.

    Args:
        metadata: Execution state metadata dictionary from AgentRuntime result.
    """
    meta = metadata or {}

    router_node = meta.get("router_node", "analytics_query")
    planner_rule = meta.get("planner_rule", "aggregate.mean")
    tool_name = meta.get("tool_name", "analytics.aggregate")
    engine_provider = meta.get("engine_provider", "PandasProvider")
    retrieved_cols = meta.get("retrieved_columns", ["salary"])
    cols_str = (
        ", ".join(retrieved_cols) if isinstance(retrieved_cols, list) else str(retrieved_cols)
    )
    latency_ms = meta.get("latency_ms", 320)
    iteration_count = meta.get("iteration_count", 1)
    thread_id = meta.get("thread_id", "thread_001")

    with st.expander("⚡ Execution Trace & Orchestration Details", expanded=False):
        trace_html = f"""
        <div class="execution-details-card">
            <div class="execution-row">
                <span class="execution-key">Router Node:</span>
                <span class="execution-val">{router_node}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Planner Capability:</span>
                <span class="execution-val">{planner_rule}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Bound Tool:</span>
                <span class="execution-val">{tool_name}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Execution Engine:</span>
                <span class="execution-val" style="color: #d0bcff;">{engine_provider}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Retrieved Column Embeddings:</span>
                <span class="execution-val">{cols_str}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Iteration Count:</span>
                <span class="execution-val">{iteration_count}</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Execution Latency:</span>
                <span class="execution-val">{latency_ms} ms</span>
            </div>
            <div class="execution-row">
                <span class="execution-key">Session Thread ID:</span>
                <span class="execution-val" style="color: #869397;">{thread_id}</span>
            </div>
        </div>
        """
        st.markdown(trace_html, unsafe_allow_html=True)


__all__ = ["render_execution_trace"]
