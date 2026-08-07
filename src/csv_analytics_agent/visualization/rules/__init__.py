"""Visualization recommendation rules grouped by analytical purpose."""

from csv_analytics_agent.visualization.rules.categorical import (
    recommend_bar,
    recommend_categorical_rules,
    recommend_pie,
)
from csv_analytics_agent.visualization.rules.distribution import (
    recommend_boxplot,
    recommend_distribution_rules,
    recommend_histogram,
)
from csv_analytics_agent.visualization.rules.relationship import (
    recommend_heatmap,
    recommend_relationship_rules,
    recommend_scatter,
)
from csv_analytics_agent.visualization.rules.temporal import (
    recommend_line,
    recommend_temporal_rules,
)

__all__ = [
    "recommend_bar",
    "recommend_boxplot",
    "recommend_categorical_rules",
    "recommend_distribution_rules",
    "recommend_heatmap",
    "recommend_histogram",
    "recommend_line",
    "recommend_pie",
    "recommend_relationship_rules",
    "recommend_scatter",
    "recommend_temporal_rules",
]
