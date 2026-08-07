"""Pure functions for computing column-level statistical metrics."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    is_string_dtype,
)

from csv_analytics_agent.profiler.models import (
    CategoricalStatistics,
    DatetimeStatistics,
    NumericStatistics,
)


def _to_float(val: Any) -> float | None:
    """Safely convert scalar pandas or numpy value to a Python float."""
    if val is None or pd.isna(val):
        return None
    return float(val)


def calculate_numeric_statistics(series: pd.Series) -> NumericStatistics | None:
    """Calculate summary statistics for a numeric pandas Series.

    Args:
        series: Input pandas Series.

    Returns:
        NumericStatistics model or None if series is non-numeric or empty.
    """
    if is_bool_dtype(series.dtype) or not is_numeric_dtype(series.dtype):
        return None

    clean_series = series.dropna()
    if clean_series.empty:
        return None

    std_val = clean_series.std() if len(clean_series) > 1 else 0.0
    var_val = clean_series.var() if len(clean_series) > 1 else 0.0

    return NumericStatistics(
        mean=_to_float(clean_series.mean()),
        median=_to_float(clean_series.median()),
        std=_to_float(std_val),
        variance=_to_float(var_val),
        min=_to_float(clean_series.min()),
        max=_to_float(clean_series.max()),
        q1=_to_float(clean_series.quantile(0.25)),
        q3=_to_float(clean_series.quantile(0.75)),
    )


def calculate_categorical_statistics(series: pd.Series) -> CategoricalStatistics | None:
    """Calculate summary statistics for a categorical or text pandas Series.

    Args:
        series: Input pandas Series.

    Returns:
        CategoricalStatistics model or None if series is numeric or datetime.
    """
    dtype = series.dtype
    is_categorical_type = (
        is_string_dtype(dtype)
        or is_object_dtype(dtype)
        or is_bool_dtype(dtype)
        or isinstance(dtype, pd.CategoricalDtype)
    )

    if not is_categorical_type:
        return None

    clean_series = series.dropna()
    category_count = int(series.nunique(dropna=True))

    if clean_series.empty:
        return CategoricalStatistics(
            mode=None,
            frequency=None,
            category_count=category_count,
        )

    mode_series = clean_series.mode()
    mode_val = str(mode_series.iloc[0]) if not mode_series.empty else None

    value_counts = clean_series.value_counts()
    top_freq = int(value_counts.iloc[0]) if not value_counts.empty else None

    return CategoricalStatistics(
        mode=mode_val,
        frequency=top_freq,
        category_count=category_count,
    )


def calculate_datetime_statistics(series: pd.Series) -> DatetimeStatistics | None:
    """Calculate summary statistics for a datetime pandas Series.

    Args:
        series: Input pandas Series.

    Returns:
        DatetimeStatistics model or None if series is not datetime.
    """
    if not is_datetime64_any_dtype(series.dtype):
        return None

    clean_series = series.dropna()
    if clean_series.empty:
        return None

    min_val = clean_series.min()
    max_val = clean_series.max()

    min_str = min_val.isoformat() if hasattr(min_val, "isoformat") else str(min_val)
    max_str = max_val.isoformat() if hasattr(max_val, "isoformat") else str(max_val)

    return DatetimeStatistics(
        earliest=min_str,
        latest=max_str,
    )
