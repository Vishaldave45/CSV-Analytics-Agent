"""Dataset profiler orchestrator for csv_analytics_agent."""

from __future__ import annotations

import pandas as pd

from csv_analytics_agent.profiler.models import (
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
)
from csv_analytics_agent.profiler.statistics import (
    calculate_categorical_statistics,
    calculate_datetime_statistics,
    calculate_numeric_statistics,
)


class DatasetProfiler:
    """Orchestrates dataset profiling for pandas DataFrames."""

    def profile(self, dataframe: pd.DataFrame) -> DatasetProfile:
        """Generate a complete profile for an input pandas DataFrame.

        Args:
            dataframe: Input pandas DataFrame to analyze.

        Returns:
            DatasetProfile model containing summary, columns, missing, and duplicate metadata.
        """
        summary = self._build_summary(dataframe)
        missing = self._build_missing_summary(dataframe)
        duplicates = self._build_duplicate_summary(dataframe)
        columns = self._build_column_profiles(dataframe)

        return DatasetProfile(
            summary=summary,
            columns=columns,
            missing=missing,
            duplicates=duplicates,
        )

    def _build_summary(self, dataframe: pd.DataFrame) -> DatasetSummary:
        """Calculate dataset-level row count, column count, and memory usage."""
        memory_usage = int(dataframe.memory_usage(deep=True).sum())
        return DatasetSummary(
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            memory_usage_bytes=memory_usage,
        )

    def _build_missing_summary(self, dataframe: pd.DataFrame) -> MissingSummary:
        """Calculate total missing values and count of columns with missing data."""
        missing_per_column = dataframe.isna().sum()
        total_missing = int(missing_per_column.sum())
        columns_with_missing = int((missing_per_column > 0).sum())

        return MissingSummary(
            total_missing_values=total_missing,
            columns_with_missing=columns_with_missing,
        )

    def _build_duplicate_summary(self, dataframe: pd.DataFrame) -> DuplicateSummary:
        """Calculate count of duplicate rows."""
        duplicate_count = int(dataframe.duplicated().sum())
        return DuplicateSummary(duplicate_rows=duplicate_count)

    def _build_column_profiles(self, dataframe: pd.DataFrame) -> list[ColumnProfile]:
        """Build column-level metadata profiles for all columns in DataFrame."""
        profiles: list[ColumnProfile] = []
        total_rows = len(dataframe)

        for col_name in dataframe.columns:
            series = dataframe[col_name]
            missing_count = int(series.isna().sum())
            missing_pct = 0.0 if total_rows == 0 else (missing_count / total_rows) * 100.0
            unique_count = int(series.nunique(dropna=True))

            numeric_stats = calculate_numeric_statistics(series)
            categorical_stats = calculate_categorical_statistics(series)
            datetime_stats = calculate_datetime_statistics(series)

            profile = ColumnProfile(
                name=str(col_name),
                dtype=str(series.dtype),
                missing_count=missing_count,
                missing_percentage=missing_pct,
                unique_count=unique_count,
                numeric=numeric_stats,
                categorical=categorical_stats,
                datetime=datetime_stats,
            )
            profiles.append(profile)

        return profiles