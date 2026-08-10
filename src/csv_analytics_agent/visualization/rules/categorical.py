"""Categorical visualization recommendation rules."""

from __future__ import annotations

from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)


def recommend_bar(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a bar chart for categorical data, optionally against a numeric column.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a bar chart, or None if no suitable categorical column exists.
    """
    cat_cols = [
        col
        for col in profile.columns
        if col.categorical is not None or (col.numeric is None and col.datetime is None)
    ]
    if not cat_cols:
        return None

    target_cat = cat_cols[0]
    numeric_cols = [col for col in profile.columns if col.numeric is not None]

    if numeric_cols:
        target_num = numeric_cols[0]
        return ChartSpecification(
            chart_type=ChartType.BAR,
            title=f"{target_num.name} by {target_cat.name}",
            x_axis=Axis(column=target_cat.name, label=target_cat.name),
            y_axis=Axis(column=target_num.name, label=target_num.name),
            description=(
                f"Bar chart comparing aggregated '{target_num.name}' values across "
                f"categories in '{target_cat.name}'."
            ),
        )

    return ChartSpecification(
        chart_type=ChartType.BAR,
        title=f"Category Counts for {target_cat.name}",
        x_axis=Axis(column=target_cat.name, label=target_cat.name),
        y_axis=None,
        description=f"Bar chart showing category frequencies for '{target_cat.name}'.",
    )


def recommend_pie(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a pie chart for low-cardinality categorical data.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a pie chart, or None if no low-cardinality category exists.
    """
    cat_cols = [
        col
        for col in profile.columns
        if (col.categorical is not None or (col.numeric is None and col.datetime is None))
        and 2 <= col.unique_count <= 7
    ]
    if not cat_cols:
        return None

    target_cat = cat_cols[0]
    return ChartSpecification(
        chart_type=ChartType.PIE,
        title=f"Proportions of {target_cat.name}",
        x_axis=Axis(column=target_cat.name, label=target_cat.name),
        y_axis=None,
        description=(
            f"Pie chart visualizing proportional breakdown across "
            f"categories in '{target_cat.name}'."
        ),
    )


def recommend_categorical_rules(profile: DatasetProfile) -> list[ChartSpecification]:
    """Evaluate all categorical recommendation rules.

    Args:
        profile: Dataset profile metadata.

    Returns:
        List of generated categorical chart specifications.
    """
    specs: list[ChartSpecification] = []

    bar_spec = recommend_bar(profile)
    if bar_spec is not None:
        specs.append(bar_spec)

    pie_spec = recommend_pie(profile)
    if pie_spec is not None:
        specs.append(pie_spec)

    return specs
