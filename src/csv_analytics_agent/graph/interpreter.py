"""Result Interpreter module for converting raw ExecutionResults into rich analytical responses.

This module provides the analytical interpretation layer that transforms computed numbers
and grouped dictionaries into structured summaries, key comparisons, markdown tables,
and automatically coupled visual charts.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.message_utils import normalize_message_content
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)
from csv_analytics_agent.visualization.renderer import render_chart


class AnalyticalResponse(BaseModel):
    """Structured analytical response container.

    Attributes:
        title: Title of the analytical finding.
        direct_answer: Concise, direct natural-language answer to the user's question.
        summary: Narrative summary of key data patterns and rankings.
        markdown_table: Cleanly formatted Markdown table of data.
        comparisons: List of key pairwise comparisons, deltas, and percentages.
        chart_spec: Optional automatically coupled ChartSpecification.
        chart_bytes: Optional rendered PNG chart bytes.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = Field(..., min_length=1)
    direct_answer: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    markdown_table: str | None = Field(default=None)
    comparisons: list[str] = Field(default_factory=list)
    chart_spec: ChartSpecification | None = Field(default=None)
    chart_bytes: bytes | None = Field(default=None)

    def to_markdown(self) -> str:
        """Render complete structured analytical response into GitHub-flavored Markdown."""
        lines: list[str] = []

        lines.append(f"### 📊 {self.title}\n")
        lines.append(f"{self.direct_answer}\n")

        if self.markdown_table:
            lines.append(self.markdown_table.strip())
            lines.append("")

        if self.summary:
            lines.append(f"**Summary:**\n{self.summary}\n")

        if self.comparisons:
            lines.append("**Key Comparisons & Takeaways:**")
            for comp in self.comparisons:
                lines.append(f"- {comp}")
            lines.append("")

        if self.chart_bytes:
            lines.append("#### 📈 Visual Chart")
            lines.append("> *Chart generated and displayed below.*\n")

        return "\n".join(lines)


def _format_number(val: float) -> str:
    """Format numeric float into a clean readable string."""
    if val.is_integer():
        return f"{int(val):,}"
    if abs(val) >= 100:
        return f"{val:,.2f}"
    return f"{val:.2f}"


def _format_dict_table(data_dict: dict[str, Any], key_header: str, val_header: str) -> str:
    """Format a key-value dictionary into a Markdown table."""
    lines = [
        f"| {key_header} | {val_header} |",
        f"| :--- | {'---:' if val_header else ':---'} |",
    ]
    for k, v in data_dict.items():
        if isinstance(v, (int, float)):
            v_str = f"**{_format_number(float(v))}**"
        else:
            v_str = str(v)
        lines.append(f"| {k} | {v_str} |")
    return "\n".join(lines)


def _interpret_grouped_data(
    user_query: str,
    data_dict: dict[str, Any],
    result: ExecutionResult,
    df: pd.DataFrame,
    llm: BaseLLM | None = None,
) -> AnalyticalResponse:
    """Interpret grouped aggregation dictionary into rich analytical response with chart."""
    by_col = result.metadata.get("by") or result.metadata.get("column") or "Category"
    target_col = result.metadata.get("target") or "Value"
    op = result.metadata.get("operation") or "count"

    # Convert numeric values for sorting and comparison
    numeric_items: list[tuple[str, float]] = []
    for k, v in data_dict.items():
        try:
            numeric_items.append((str(k), float(v)))
        except (ValueError, TypeError):
            pass

    # Sort descending by value
    sorted_items = sorted(numeric_items, key=lambda x: x[1], reverse=True)
    sorted_dict = {k: v for k, v in sorted_items} if sorted_items else data_dict

    # 1. Build Markdown Table
    val_label = "Count" if op == "count" else f"{op.title()} {target_col.title()}"
    table_md = _format_dict_table(
        sorted_dict,
        key_header=str(by_col).replace("_", " ").title(),
        val_header=val_label,
    )

    # 2. Compute Deterministic Comparisons & Deltas
    comparisons: list[str] = []
    summary_lines: list[str] = []
    direct_answer = ""

    if len(sorted_items) >= 2:
        top_name, top_val = sorted_items[0]
        bot_name, bot_val = sorted_items[-1]
        delta_top_bot = top_val - bot_val
        pct_top_bot = (delta_top_bot / bot_val * 100) if bot_val != 0 else 0.0
        top_str = _format_number(top_val)
        bot_str = _format_number(bot_val)

        summary_lines.append(
            f"**{top_name}** has the highest {val_label.lower()} with **{top_str}**, "
            f"while **{bot_name}** has the lowest with **{bot_str}**."
        )

        comparisons.append(
            f"**{top_name} vs {bot_name}**: +{_format_number(delta_top_bot)} (+{pct_top_bot:.1f}%)"
        )

        # Runner up comparison
        if len(sorted_items) >= 3:
            second_name, second_val = sorted_items[1]
            diff_1_2 = top_val - second_val
            comparisons.append(
                f"**{top_name} vs {second_name}** (1st vs 2nd): +{_format_number(diff_1_2)}"
            )

        # Check for ties or equals
        val_counts: dict[float, list[str]] = {}
        for k, v in sorted_items:
            val_counts.setdefault(v, []).append(k)

        for val, tied_keys in val_counts.items():
            if len(tied_keys) > 1:
                comparisons.append(f"**{' and '.join(tied_keys)}**: Equal ({_format_number(val)})")

        direct_answer = (
            f"**{top_name}** leads across all {len(sorted_items)} {by_col.lower()}s with "
            f"**{_format_number(top_val)} {val_label.lower()}**."
        )
    elif sorted_items:
        top_name, top_val = sorted_items[0]
        direct_answer = f"**{top_name}**: **{_format_number(top_val)} {val_label.lower()}**."
        summary_lines.append(f"Recorded **{_format_number(top_val)}** for {top_name}.")

    summary = " ".join(summary_lines)

    # 3. LLM Synthesis for Context-Specific Direct Answer (if LLM is available)
    if llm is not None and user_query:
        try:
            sys_msg = SystemMessage(
                content=(
                    "You are an expert data analyst. Based strictly on the data breakdown, "
                    "write a clear, direct, 1-2 sentence answer to the user's specific question. "
                    "Be exact with names and numbers."
                )
            )
            user_prompt = (
                f"User Question: '{user_query}'\n"
                f"Data Breakdown: {sorted_dict}\n"
                f"Key Facts: Top: {sorted_items[0] if sorted_items else 'N/A'}, "
                f"Bottom: {sorted_items[-1] if sorted_items else 'N/A'}\n"
                f"Answer:"
            )
            response = llm.invoke([sys_msg, HumanMessage(content=user_prompt)])
            llm_text = normalize_message_content(getattr(response, "content", ""))
            if llm_text:
                direct_answer = llm_text
        except Exception:
            pass  # Fall back cleanly to deterministic direct_answer

    # 4. Auto-Couple Visual Chart
    chart_spec: ChartSpecification | None = None
    chart_bytes: bytes | None = None
    if str(by_col) in df.columns:
        # Determine chart type: line for dates/trends, bar for categories
        is_date_col = "date" in str(by_col).lower() or "time" in str(by_col).lower()
        c_type = ChartType.LINE if is_date_col else ChartType.BAR

        chart_spec = ChartSpecification(
            chart_type=c_type,
            title=f"{val_label} by {str(by_col).replace('_', ' ').title()}",
            x_axis=Axis(column=str(by_col)),
            y_axis=Axis(column=str(target_col)) if str(target_col) in df.columns else None,
            description=f"Comparison of {val_label.lower()} across {by_col}.",
        )
        try:
            chart_bytes = render_chart(chart_spec, df)
        except Exception:
            chart_bytes = None

    title_text = f"{val_label} by {str(by_col).replace('_', ' ').title()}"

    return AnalyticalResponse(
        title=title_text,
        direct_answer=direct_answer,
        summary=summary,
        markdown_table=table_md,
        comparisons=comparisons,
        chart_spec=chart_spec,
        chart_bytes=chart_bytes,
    )


def _format_dataframe_table(res_df: pd.DataFrame, max_rows: int = 10) -> str:
    """Pure-Python DataFrame to Markdown table formatter without external dependencies."""
    preview_df = res_df.head(max_rows)
    cols = [str(c) for c in preview_df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join([":---"] * len(cols)) + " |",
    ]
    for _, row in preview_df.iterrows():
        row_vals = [str(val) for val in row.values]
        lines.append("| " + " | ".join(row_vals) + " |")
    return "\n".join(lines)


def _interpret_dataframe_result(
    user_query: str,
    res_df: pd.DataFrame,
    result: ExecutionResult,
) -> AnalyticalResponse:
    """Interpret DataFrame result (filter, top_n, sort) into analytical response."""
    cap_name = result.capability_name.title()
    row_count = len(res_df)

    # Format table for up to top 10 rows
    table_md = _format_dataframe_table(res_df, max_rows=10)

    direct_answer = f"Found **{row_count:,} matching record{'s' if row_count != 1 else ''}**."
    summary = f"Operation `{result.capability_name}` returned {row_count} rows. {result.message}"

    return AnalyticalResponse(
        title=f"{cap_name} Results ({row_count:,} rows)",
        direct_answer=direct_answer,
        summary=summary,
        markdown_table=table_md,
        comparisons=[],
        chart_spec=None,
        chart_bytes=None,
    )


def _interpret_scalar_result(
    user_query: str,
    val: Any,
    result: ExecutionResult,
    df: pd.DataFrame,
) -> AnalyticalResponse:
    """Interpret scalar calculation (aggregate, count, mean)."""
    col = result.metadata.get("column", "Metric")
    op = result.metadata.get("operation", "result")

    if isinstance(val, (int, float)):
        val_formatted = _format_number(float(val))
    else:
        val_formatted = str(val)

    direct_answer = f"The **{op}** for **{col}** is **{val_formatted}**."
    summary = result.message

    return AnalyticalResponse(
        title=f"{op.title()} Calculation: {col.title()}",
        direct_answer=direct_answer,
        summary=summary,
        markdown_table=None,
        comparisons=[],
        chart_spec=None,
        chart_bytes=None,
    )


def interpret_execution_result(
    user_query: str,
    result: ExecutionResult,
    df: pd.DataFrame,
    llm: BaseLLM | None = None,
) -> AnalyticalResponse:
    """Transform ExecutionResult into a structured, user-friendly AnalyticalResponse.

    Args:
        user_query: The active natural language question from the user.
        result: ExecutionResult payload from Stage 5 Execution Framework.
        df: Target pandas DataFrame context.
        llm: Optional BaseLLM provider instance for contextual narrative synthesis.

    Returns:
        Structured AnalyticalResponse object with answers, tables, comparisons, and charts.
    """
    # 1. Error / Failure Case
    if result.status == ExecutionStatus.FAILED:
        return AnalyticalResponse(
            title=f"Execution Failed: {result.capability_name.title()}",
            direct_answer=f"⚠️ Could not complete analytical operation: {result.message}",
            summary=result.message,
            markdown_table=None,
            comparisons=[],
            chart_spec=None,
            chart_bytes=None,
        )

    # 2. Image Bytes (Render Visualization)
    if isinstance(result.data, bytes):
        chart_type = result.metadata.get("chart_type", "visualization")
        title = result.metadata.get("title", f"{chart_type.title()} Chart")
        return AnalyticalResponse(
            title=title,
            direct_answer=f"Generated and rendered **{chart_type} chart**.",
            summary=result.message,
            markdown_table=None,
            comparisons=[],
            chart_spec=None,
            chart_bytes=result.data,
        )

    # 3. Group / Dictionary Data
    if isinstance(result.data, dict):
        return _interpret_grouped_data(
            user_query=user_query,
            data_dict=result.data,
            result=result,
            df=df,
            llm=llm,
        )

    # 4. DataFrame Data (Filter, Sort, Top N)
    if isinstance(result.data, pd.DataFrame):
        return _interpret_dataframe_result(
            user_query=user_query,
            res_df=result.data,
            result=result,
        )

    # 5. Scalar / Primitive Data (Aggregate)
    return _interpret_scalar_result(
        user_query=user_query,
        val=result.data,
        result=result,
        df=df,
    )


__all__ = [
    "AnalyticalResponse",
    "interpret_execution_result",
]
