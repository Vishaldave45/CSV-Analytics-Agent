"""Distribution visualization recommendation rules."""

from __future__ import annotations

from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)


def recommend_histogram(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a histogram for the first suitable numeric column.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a histogram, or None if no numeric column exists.
    """
    numeric_cols = [col for col in profile.columns if col.numeric is not None]
    if not numeric_cols:
        return None

    target = numeric_cols[0]
    return ChartSpecification(
        chart_type=ChartType.HISTOGRAM,
        title=f"Distribution of {target.name}",
        x_axis=Axis(column=target.name, label=target.name),
        y_axis=Axis(column="frequency", label="Frequency"),
        description=(
            f"Histogram showing the frequency distribution of continuous numeric "
            f"values in '{target.name}'."
        ),
    )


def recommend_boxplot(profile: DatasetProfile) -> ChartSpecification | None:
    """Recommend a boxplot for numeric column distribution, optionally grouped by category.

    Args:
        profile: Dataset profile metadata.

    Returns:
        ChartSpecification for a boxplot, or None if no numeric column exists.
    """
    numeric_cols = [col for col in profile.columns if col.numeric is not None]
    if not numeric_cols:
        return None

    target_num = numeric_cols[0]
    cat_cols = [
        col
        for col in profile.columns
        if col.categorical is not None or (col.numeric is None and col.datetime is None)
    ]

    if cat_cols:
        target_cat = cat_cols[0]
        return ChartSpecification(
            chart_type=ChartType.BOXPLOT,
            title=f"Boxplot of {target_num.name} by {target_cat.name}",
            x_axis=Axis(column=target_cat.name, label=target_cat.name),
            y_axis=Axis(column=target_num.name, label=target_num.name),
            description=(
                f"Boxplot displaying summary statistics and outlier spread of '{target_num.name}' "
                f"grouped by '{target_cat.name}'."
            ),
        )

    return ChartSpecification(
        chart_type=ChartType.BOXPLOT,
        title=f"Boxplot of {target_num.name}",
        x_axis=Axis(column=target_num.name, label=target_num.name),
        y_axis=None,
        description=(
            f"Boxplot displaying statistical quartiles and outliers for '{target_num.name}'."
        ),
    )


def recommend_distribution_rules(profile: DatasetProfile) -> list[ChartSpecification]:
    """Evaluate all distribution recommendation rules.

    Args:
        profile: Dataset profile metadata.

    Returns:
        List of generated distribution chart specifications.
    """
    specs: list[ChartSpecification] = []

    hist_spec = recommend_histogram(profile)
    if hist_spec is not None:
        specs.append(hist_spec)

    box_spec = recommend_boxplot(profile)
    if box_spec is not None:
        specs.append(box_spec)

    return specs
