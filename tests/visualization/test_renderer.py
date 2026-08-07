"""Unit tests for Matplotlib visualization renderer."""

from pathlib import Path

import pandas as pd
import pytest

from csv_analytics_agent.visualization import (
    Axis,
    ChartSpecification,
    ChartType,
    VisualizationError,
    render_chart,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 45, 50],
        "salary": [50000, 60000, 75000, 90000, 110000, 130000],
        "department": ["HR", "IT", "IT", "HR", "Sales", "IT"],
        "date": pd.date_range("2026-01-01", periods=6, freq="D"),
    })


def test_render_histogram(sample_df: pd.DataFrame) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.HISTOGRAM,
        title="Age Distribution",
        x_axis=Axis(column="age"),
        description="Histogram of ages",
    )
    img_bytes = render_chart(spec, sample_df)
    assert len(img_bytes) > 0
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_bar_chart(sample_df: pd.DataFrame) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.BAR,
        title="Salary by Department",
        x_axis=Axis(column="department"),
        y_axis=Axis(column="salary"),
        description="Bar chart of department salaries",
    )
    img_bytes = render_chart(spec, sample_df)
    assert len(img_bytes) > 0
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_line_chart(sample_df: pd.DataFrame) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.LINE,
        title="Salary over Time",
        x_axis=Axis(column="date"),
        y_axis=Axis(column="salary"),
        description="Line chart over date",
    )
    img_bytes = render_chart(spec, sample_df)
    assert len(img_bytes) > 0


def test_render_scatter_chart(sample_df: pd.DataFrame) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.SCATTER,
        title="Age vs Salary",
        x_axis=Axis(column="age"),
        y_axis=Axis(column="salary"),
        description="Scatter plot of age vs salary",
    )
    img_bytes = render_chart(spec, sample_df)
    assert len(img_bytes) > 0


def test_render_chart_save_to_disk(sample_df: pd.DataFrame, tmp_path: Path) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.PIE,
        title="Department Breakdown",
        x_axis=Axis(column="department"),
        description="Pie chart",
    )
    out_file = tmp_path / "chart.png"
    img_bytes = render_chart(spec, sample_df, save_path=out_file)

    assert out_file.exists()
    assert out_file.stat().st_size > 0
    assert out_file.read_bytes() == img_bytes


def test_render_missing_column_raises_error(sample_df: pd.DataFrame) -> None:
    spec = ChartSpecification(
        chart_type=ChartType.HISTOGRAM,
        title="Invalid Column",
        x_axis=Axis(column="non_existent_column"),
        description="Invalid spec",
    )
    with pytest.raises(VisualizationError):
        render_chart(spec, sample_df)
