"""Unit tests for Stage 7.11 Result Interpreter module."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.interpreter import (
    AnalyticalResponse,
    interpret_execution_result,
)


@pytest.fixture
def sample_sales_df() -> pd.DataFrame:
    """Fixture with category, revenue, and order_date columns."""
    return pd.DataFrame(
        {
            "category": [
                "Sports",
                "Sports",
                "Books",
                "Books",
                "Apparel",
                "Electronics",
                "Home & Kitchen",
            ],
            "order_id": [1, 2, 3, 4, 5, 6, 7],
            "unit_price": [41.48, 41.48, 19.60, 19.60, 48.79, 97.10, 73.04],
            "order_date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-06",
                "2024-01-07",
            ],
        }
    )


def test_interpret_grouped_order_counts(sample_sales_df: pd.DataFrame) -> None:
    """Verify rich interpretation of order counts across categories with chart generation."""
    raw_data = {
        "Apparel": 104,
        "Books": 105,
        "Electronics": 92,
        "Home & Kitchen": 92,
        "Sports": 115,
    }
    result = ExecutionResult(
        capability_name="group",
        status=ExecutionStatus.SUCCESS,
        message="Grouped by 'category' calculating count on 'order_id' (5 groups).",
        data=raw_data,
        metadata={"by": "category", "target": "order_id", "operation": "count"},
    )

    resp = interpret_execution_result(
        user_query="Compare order counts across the 5 categories.",
        result=result,
        df=sample_sales_df,
    )

    assert isinstance(resp, AnalyticalResponse)
    assert "Count by Category" in resp.title
    assert "Sports" in resp.direct_answer
    assert "115" in resp.direct_answer

    # Verify Markdown Table structure & descending sort
    assert resp.markdown_table is not None
    assert "| Category | Count |" in resp.markdown_table
    lines = resp.markdown_table.strip().split("\n")
    # First data row after header & separator should be Sports (115)
    assert "Sports" in lines[2]
    assert "115" in lines[2]

    # Verify comparisons & deltas
    assert len(resp.comparisons) >= 2
    # Top vs bottom delta
    assert any("Sports vs" in c and "+23" in c for c in resp.comparisons)
    # Tied categories (Electronics and Home & Kitchen: Equal)
    assert any("Electronics and Home & Kitchen" in c and "Equal" in c for c in resp.comparisons)

    # Verify chart auto-coupling
    assert resp.chart_spec is not None
    assert resp.chart_bytes is not None
    assert isinstance(resp.chart_bytes, bytes)
    assert len(resp.chart_bytes) > 0

    # Verify to_markdown format
    md_output = resp.to_markdown()
    assert "### 📊" in md_output
    assert "Key Comparisons & Takeaways:" in md_output


def test_interpret_grouped_unit_price_comparison(sample_sales_df: pd.DataFrame) -> None:
    """Verify interpretation of unit price comparisons across categories."""
    raw_data = {
        "Apparel": 48.79,
        "Books": 19.60,
        "Electronics": 97.10,
        "Home & Kitchen": 73.04,
        "Sports": 41.48,
    }
    result = ExecutionResult(
        capability_name="group",
        status=ExecutionStatus.SUCCESS,
        message="Grouped by 'category' calculating mean on 'unit_price' (5 groups).",
        data=raw_data,
        metadata={"by": "category", "target": "unit_price", "operation": "mean"},
    )

    resp = interpret_execution_result(
        user_query=(
            "Does Books have a lower average unit_price than every other category, "
            "or is it close to Apparel?"
        ),
        result=result,
        df=sample_sales_df,
    )

    assert isinstance(resp, AnalyticalResponse)
    assert resp.markdown_table is not None
    assert "Electronics" in resp.direct_answer or "Electronics" in resp.summary
    assert resp.chart_bytes is not None


def test_interpret_scalar_aggregate(sample_sales_df: pd.DataFrame) -> None:
    """Verify interpretation of single scalar metric."""
    result = ExecutionResult(
        capability_name="aggregate",
        status=ExecutionStatus.SUCCESS,
        message="Calculated mean on 'unit_price': 54.20",
        data=54.20,
        metadata={"column": "unit_price", "operation": "mean"},
    )

    resp = interpret_execution_result(
        user_query="What is the average unit price?",
        result=result,
        df=sample_sales_df,
    )

    assert isinstance(resp, AnalyticalResponse)
    assert "54.20" in resp.direct_answer
    assert "Mean Calculation: Unit_Price" in resp.title


def test_interpret_dataframe_filter(sample_sales_df: pd.DataFrame) -> None:
    """Verify interpretation of filtered DataFrame."""
    filtered_df = sample_sales_df[sample_sales_df["category"] == "Sports"]
    result = ExecutionResult(
        capability_name="filter",
        status=ExecutionStatus.SUCCESS,
        message="Filtered 'category' eq Sports. Rows returned: 2",
        data=filtered_df,
    )

    resp = interpret_execution_result(
        user_query="Filter orders in Sports category",
        result=result,
        df=sample_sales_df,
    )

    assert isinstance(resp, AnalyticalResponse)
    assert "2 matching records" in resp.direct_answer
    assert resp.markdown_table is not None
    assert "| category | order_id |" in resp.markdown_table


def test_interpret_failed_result(sample_sales_df: pd.DataFrame) -> None:
    """Verify interpretation of failed execution."""
    result = ExecutionResult(
        capability_name="group",
        status=ExecutionStatus.FAILED,
        message="Column 'unknown_col' not found.",
        data=None,
    )

    resp = interpret_execution_result(
        user_query="Group by unknown column",
        result=result,
        df=sample_sales_df,
    )

    assert "Execution Failed" in resp.title
    assert "⚠️ Could not complete" in resp.direct_answer
