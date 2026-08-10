"""Deterministic data preprocessing and semantic type coercion engine."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class CoercionReport(BaseModel):
    """Structured report documenting the outcome of dataframe type coercion."""

    model_config = ConfigDict(frozen=True)

    numeric_coerced: list[str] = Field(default_factory=list)
    datetime_coerced: list[str] = Field(default_factory=list)
    failed_conversions: dict[str, int] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Return summary dictionary for structured logging."""
        return {
            "numeric_coerced": self.numeric_coerced,
            "datetime_coerced": self.datetime_coerced,
            "failed_conversions": self.failed_conversions,
        }


def coerce_dataframe(
    df: pd.DataFrame,
    threshold: float = 0.9,
) -> tuple[pd.DataFrame, CoercionReport]:
    """Detect and coerce formatted numeric strings and date-like strings in a DataFrame.

    Operates as a pure function returning a new modified copy of the DataFrame and
    a CoercionReport.

    Handles:
    - Currency formatted strings: "$1,234.56", "€500", "£99.99" -> float
    - Percent formatted strings: "15.5%", "90%" -> 0.155 / 0.9
    - Commas in numbers: "1,000,000" -> float/int
    - Date and timestamp strings: "2024-01-15", "15/01/2024" -> datetime64[ns]

    Args:
        df: Input pandas DataFrame.
        threshold: Minimum fraction of non-null values that must successfully convert
                   for the column to be coerced (default 0.9).

    Returns:
        Tuple of (coerced DataFrame, CoercionReport).
    """
    coerced_df = df.copy()
    numeric_coerced: list[str] = []
    datetime_coerced: list[str] = []
    failed_conversions: dict[str, int] = {}

    date_pattern = re.compile(r"[-/\s.]|[a-zA-Z]{3,}")

    for col in coerced_df.columns:
        series = coerced_df[col]

        # Only process object / string / category columns
        if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
            continue

        non_null = series.dropna()
        if len(non_null) == 0:
            continue

        str_vals = non_null.astype(str).str.strip()

        # 1. Attempt Numeric / Currency / Percentage Coercion
        # Check for currency symbols or percent signs
        is_percent = str_vals.str.endswith("%")
        has_currency = str_vals.str.contains(r"[\$,€£¥₹]", regex=True)
        has_commas = str_vals.str.contains(r",", regex=True)

        if has_currency.any() or has_commas.any() or is_percent.any():
            cleaned_num_str = str_vals.str.replace(r"[\$,€£¥₹\s]", "", regex=True)
            if is_percent.mean() >= threshold:
                cleaned_num_str = cleaned_num_str.str.rstrip("%")
                numeric_series = pd.to_numeric(cleaned_num_str, errors="coerce") / 100.0
            else:
                numeric_series = pd.to_numeric(cleaned_num_str, errors="coerce")

            valid_ratio = numeric_series.notna().mean()
            if valid_ratio >= threshold:
                raw_str = series.astype(str).str.strip()
                full_cleaned = raw_str.str.replace(r"[\$,€£¥₹\s]", "", regex=True)
                if is_percent.mean() >= threshold:
                    full_cleaned = full_cleaned.str.rstrip("%")
                    full_coerced = pd.to_numeric(full_cleaned, errors="coerce") / 100.0
                else:
                    full_coerced = pd.to_numeric(full_cleaned, errors="coerce")

                failed_count = int((series.notna() & full_coerced.isna()).sum())
                coerced_df[col] = full_coerced
                numeric_coerced.append(str(col))
                if failed_count > 0:
                    failed_conversions[str(col)] = failed_count
                continue

        # 2. Attempt Datetime Coercion
        # Avoid treating pure numbers as dates
        looks_like_date = str_vals.apply(
            lambda x: bool(date_pattern.search(x) and not x.replace(".", "").isdigit())
        )
        if looks_like_date.mean() >= threshold:
            try:
                dt_series = pd.to_datetime(str_vals, format="mixed", errors="coerce")
            except ValueError:
                dt_series = pd.to_datetime(str_vals, errors="coerce")

            valid_dt_ratio = dt_series.notna().mean()
            if valid_dt_ratio >= threshold:
                try:
                    full_dt_coerced = pd.to_datetime(series, format="mixed", errors="coerce")
                except ValueError:
                    full_dt_coerced = pd.to_datetime(series, errors="coerce")

                failed_count = int((series.notna() & full_dt_coerced.isna()).sum())
                coerced_df[col] = full_dt_coerced
                datetime_coerced.append(str(col))
                if failed_count > 0:
                    failed_conversions[str(col)] = failed_count
                continue

    report = CoercionReport(
        numeric_coerced=numeric_coerced,
        datetime_coerced=datetime_coerced,
        failed_conversions=failed_conversions,
    )
    return coerced_df, report


__all__ = ["CoercionReport", "coerce_dataframe"]
