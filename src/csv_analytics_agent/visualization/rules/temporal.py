"""Temporal visualization recommendation rules."""

from __future__ import annotations

from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)


def recommend_line(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a line chart for datetime trend against a numeric column.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a line chart, or None if required temporal/numeric data is missing.
    """
    dt_cols = [col for col in profile.columns if col.datetime is not None]
    numeric_cols = [col for col in profile.columns if col.numeric is not None]

    if not dt_cols or not numeric_cols:
        return None

    target_dt = dt_cols[0]
    target_num = numeric_cols[0]

    return ChartSpecification(
        chart_type=ChartType.LINE,
        title=f"{target_num.name} over {target_dt.name}",
        x_axis=Axis(column=target_dt.name, label=target_dt.name),
        y_axis=Axis(column=target_num.name, label=target_num.name),
        description=(
            f"Line chart displaying temporal trend of '{target_num.name}' over time "
            f"dimension '{target_dt.name}'."
        ),
    )


def recommend_temporal_rules(profile: DatasetProfile) -> list[ChartSpecification]:
    """Evaluate all temporal recommendation rules.

    Args:
        profile: Dataset profile metadata.

    Returns:
        List of generated temporal chart specifications.
    """
    specs: list[ChartSpecification] = []

    line_spec = recommend_line(profile)
    if line_spec is not None:
        specs.append(line_spec)

    return specs
