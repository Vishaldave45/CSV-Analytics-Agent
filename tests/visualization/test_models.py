"""Unit tests for visualization domain models."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.visualization import (
    Axis,
    ChartSpecification,
    ChartType,
    VisualizationPlan,
)


def test_chart_type_enum_values() -> None:
    """Verify all expected ChartType enum values."""
    assert ChartType.HISTOGRAM.value == "histogram"
    assert ChartType.BAR.value == "bar"
    assert ChartType.LINE.value == "line"
    assert ChartType.SCATTER.value == "scatter"
    assert ChartType.BOXPLOT.value == "boxplot"
    assert ChartType.PIE.value == "pie"
    assert ChartType.HEATMAP.value == "heatmap"


def test_axis_model_valid() -> None:
    """Test valid Axis model creation."""
    axis = Axis(column="sales", label="Total Sales ($)")
    assert axis.column == "sales"
    assert axis.label == "Total Sales ($)"


def test_axis_model_optional_label() -> None:
    """Test Axis model without label defaults to None."""
    axis = Axis(column="age")
    assert axis.column == "age"
    assert axis.label is None


def test_axis_empty_column_validation() -> None:
    """Test Axis column validation fails on empty string."""
    with pytest.raises(ValidationError):
        Axis(column="")


def test_chart_specification_valid() -> None:
    """Test valid ChartSpecification creation."""
    spec = ChartSpecification(
        chart_type=ChartType.BAR,
        title="Sales by Region",
        x_axis=Axis(column="region", label="Region"),
        y_axis=Axis(column="sales", label="Sales ($)"),
        description="Bar chart illustrating distribution of sales across regions.",
    )
    assert spec.chart_type == ChartType.BAR
    assert spec.title == "Sales by Region"
    assert spec.x_axis.column == "region"
    assert spec.y_axis is not None
    assert spec.y_axis.column == "sales"
    assert spec.description == "Bar chart illustrating distribution of sales across regions."


def test_chart_specification_immutability() -> None:
    """Verify frozen mutation on ChartSpecification raises ValidationError."""
    spec = ChartSpecification(
        chart_type=ChartType.HISTOGRAM,
        title="Age Distribution",
        x_axis=Axis(column="age"),
        description="Histogram of ages.",
    )
    with pytest.raises(ValidationError):
        setattr(spec, "title", "Modified Title")  # noqa: B010


def test_empty_title_validation() -> None:
    """Test ChartSpecification validation fails on empty title."""
    with pytest.raises(ValidationError):
        ChartSpecification(
            chart_type=ChartType.LINE,
            title="",
            x_axis=Axis(column="date"),
            description="Line chart over time.",
        )


def test_title_max_length_validation() -> None:
    """Test ChartSpecification validation fails on title exceeding 100 characters."""
    long_title = "A" * 101
    with pytest.raises(ValidationError):
        ChartSpecification(
            chart_type=ChartType.LINE,
            title=long_title,
            x_axis=Axis(column="date"),
            description="Line chart with invalid long title.",
        )


def test_empty_description_validation() -> None:
    """Test ChartSpecification validation fails on empty description."""
    with pytest.raises(ValidationError):
        ChartSpecification(
            chart_type=ChartType.LINE,
            title="Valid Title",
            x_axis=Axis(column="date"),
            description="",
        )


def test_visualization_plan_default_alternatives() -> None:
    """Test VisualizationPlan default empty alternatives list."""
    primary = ChartSpecification(
        chart_type=ChartType.SCATTER,
        title="Price vs Area",
        x_axis=Axis(column="area"),
        y_axis=Axis(column="price"),
        description="Scatter plot comparing property area against price.",
    )
    plan = VisualizationPlan(primary=primary)
    assert plan.primary == primary
    assert plan.alternatives == []


def test_visualization_plan_with_alternatives() -> None:
    """Test VisualizationPlan with explicit list of alternative specifications."""
    primary = ChartSpecification(
        chart_type=ChartType.SCATTER,
        title="Price vs Area",
        x_axis=Axis(column="area"),
        y_axis=Axis(column="price"),
        description="Scatter plot comparing property area against price.",
    )
    alt = ChartSpecification(
        chart_type=ChartType.LINE,
        title="Price Trend by Area",
        x_axis=Axis(column="area"),
        y_axis=Axis(column="price"),
        description="Line chart showing average price by area.",
    )
    plan = VisualizationPlan(primary=primary, alternatives=[alt])
    assert plan.primary.chart_type == ChartType.SCATTER
    assert len(plan.alternatives) == 1
    assert plan.alternatives[0].chart_type == ChartType.LINE


def test_model_serialization() -> None:
    """Test Pydantic model_dump and model_dump_json serialization."""
    spec = ChartSpecification(
        chart_type=ChartType.BAR,
        title="Sales by Region",
        x_axis=Axis(column="region"),
        description="Bar chart description.",
    )
    dumped = spec.model_dump()
    assert dumped["chart_type"] == "bar"
    assert dumped["title"] == "Sales by Region"
    assert dumped["x_axis"]["column"] == "region"

    json_str = spec.model_dump_json()
    assert '"chart_type":"bar"' in json_str
