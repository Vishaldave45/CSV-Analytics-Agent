"""Unit tests for DataFrame type coercion engine and temporal visualization rule integration."""

import pandas as pd

from csv_analytics_agent.preprocessing.coercion import CoercionReport, coerce_dataframe
from csv_analytics_agent.profiler.profiler import DatasetProfiler
from csv_analytics_agent.visualization.models import ChartType
from csv_analytics_agent.visualization.rules.temporal import recommend_line


def test_coerce_currency_and_percentages() -> None:
    """Test coercion of currency and percentage formatted string columns."""
    df = pd.DataFrame(
        {
            "revenue": ["$1,200.50", "$3,400.00", "$550.25", "$9,999.99"],
            "discount_pct": ["10%", "25.5%", "0%", "50%"],
            "product": ["Widget A", "Widget B", "Widget C", "Widget D"],
        }
    )

    coerced_df, report = coerce_dataframe(df)

    assert isinstance(report, CoercionReport)
    assert "revenue" in report.numeric_coerced
    assert "discount_pct" in report.numeric_coerced
    assert "product" not in report.numeric_coerced

    assert pd.api.types.is_numeric_dtype(coerced_df["revenue"])
    assert pd.api.types.is_numeric_dtype(coerced_df["discount_pct"])
    assert coerced_df["revenue"].iloc[0] == 1200.50
    assert coerced_df["discount_pct"].iloc[0] == 0.10
    assert coerced_df["discount_pct"].iloc[1] == 0.255


def test_coerce_dates_and_temporal_rule_firing() -> None:
    """Test that date coercion allows temporal visualization rules to recommend line charts."""
    raw_df = pd.DataFrame(
        {
            "Date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-18",
            ],
            "Units_Sold": [120, 85, 45, 200, 110],
            "Revenue": [120000.0, 42500.0, 31500.0, 90000.0, 55000.0],
        }
    )

    # Before coercion, Date is object/string, so recommend_line returns None
    uncoerced_profile = DatasetProfiler().profile(raw_df)
    assert recommend_line(uncoerced_profile) is None

    # After coercion, Date becomes datetime64
    coerced_df, report = coerce_dataframe(raw_df)
    assert "Date" in report.datetime_coerced
    assert pd.api.types.is_datetime64_any_dtype(coerced_df["Date"])

    # Now profiling detects the datetime column and recommend_line successfully fires!
    coerced_profile = DatasetProfiler().profile(coerced_df)
    line_spec = recommend_line(coerced_profile)

    assert line_spec is not None
    assert line_spec.chart_type == ChartType.LINE
    assert line_spec.x_axis.column == "Date"
    assert line_spec.y_axis is not None
    assert line_spec.y_axis.column in ("Units_Sold", "Revenue")


def test_coerce_threshold_preservation() -> None:
    """Test that columns with mixed/invalid non-convertible values below threshold are preserved."""
    df = pd.DataFrame(
        {
            "mostly_text": ["$100", "Not a price", "N/A", "Unknown string"],
            "valid_numbers": ["10", "20", "30", "40"],
        }
    )

    coerced_df, report = coerce_dataframe(df, threshold=0.8)

    # mostly_text should NOT be coerced to numeric since only 25% is currency
    assert "mostly_text" not in report.numeric_coerced
    assert coerced_df["mostly_text"].iloc[1] == "Not a price"
