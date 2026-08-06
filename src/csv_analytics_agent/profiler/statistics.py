"""Statistics engine for numeric column profiling."""

from __future__ import annotations

from typing import Any

import pandas as pd

from csv_analytics_agent.profiler.models import NumericStatistics


def _to_float(val: Any) -> float | None:
    """Safely convert a scalar pandas/numpy value to a Python float."""
    if val is None or pd.isna(val):
        return None
    return float(val)


class StatisticsEngine:
    """Compute statistics for numeric columns."""

    def compute(self, series: pd.Series) -> NumericStatistics | None:
        """Compute summary statistics for a numeric pandas Series.

        Args:
            series: Input pandas Series.

        Returns:
            NumericStatistics model or None if the series is not numeric or empty.
        """
        if not pd.api.types.is_numeric_dtype(series.dtype) or series.dropna().empty:
            return None

        clean_series = series.dropna()

        std_val = clean_series.std() if len(clean_series) > 1 else 0.0
        var_val = clean_series.var() if len(clean_series) > 1 else 0.0

        return NumericStatistics(
            mean=_to_float(clean_series.mean()),
            median=_to_float(clean_series.median()),
            minimum=_to_float(clean_series.min()),
            maximum=_to_float(clean_series.max()),
            standard_deviation=_to_float(std_val),
            variance=_to_float(var_val),
            q1=_to_float(clean_series.quantile(0.25)),
            q3=_to_float(clean_series.quantile(0.75)),
        )