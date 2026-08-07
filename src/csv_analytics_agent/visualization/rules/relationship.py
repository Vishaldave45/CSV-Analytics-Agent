"""Relationship visualization recommendation rules."""

from __future__ import annotations

from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)


def recommend_scatter(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a scatter plot for two numeric columns.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a scatter plot, or None if fewer than two numeric columns exist.
    """
    numeric_cols = [col for col in profile.columns if col.numeric is not None]
    if len(numeric_cols) < 2:
        return None

    x_col = numeric_cols[0]
    y_col = numeric_cols[1]

    return ChartSpecification(
        chart_type=ChartType.SCATTER,
        title=f"{x_col.name} vs {y_col.name}",
        x_axis=Axis(column=x_col.name, label=x_col.name),
        y_axis=Axis(column=y_col.name, label=y_col.name),
        description=(
            f"Scatter plot illustrating relationship and correlation between '{x_col.name}' "
            f"and '{y_col.name}'."
        ),
    )


def recommend_heatmap(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a correlation heatmap if at least two numeric columns exist.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a heatmap, or None if fewer than two numeric columns exist.
    """
    numeric_cols = [col for col in profile.columns if col.numeric is not None]
    if len(numeric_cols) < 2:
        return None

    x_col = numeric_cols[0]
    y_col = numeric_cols[1]

    return ChartSpecification(
        chart_type=ChartType.HEATMAP,
        title="Correlation Heatmap",
        x_axis=Axis(column=x_col.name, label=x_col.name),
        y_axis=Axis(column=y_col.name, label=y_col.name),
        description="Heatmap showing pairwise correlations across dataset variables.",
    )


def recommend_relationship_rules(profile: DatasetProfile) -> list[ChartSpecification]:
    """Evaluate all relationship recommendation rules.

    Args:
        profile: Dataset profile metadata.

    Returns:
        List of generated relationship chart specifications.
    """
    specs: list[ChartSpecification] = []

    scatter_spec = recommend_scatter(profile)
    if scatter_spec is not None:
        specs.append(scatter_spec)

    heatmap_spec = recommend_heatmap(profile)
    if heatmap_spec is not None:
        specs.append(heatmap_spec)

    return specs
