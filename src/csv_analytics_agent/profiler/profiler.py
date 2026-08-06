"""Dataset profiler for csv_analytics_agent."""

from __future__ import annotations

import pandas as pd

from csv_analytics_agent.profiler.models import (
    BasicColumnInfo,
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingValueSummary,
)
from csv_analytics_agent.profiler.statistics import StatisticsEngine


class DatasetProfiler:
    """Profiles a pandas DataFrame."""

    def __init__(self, stats_engine: StatisticsEngine | None = None) -> None:
        self._stats_engine = stats_engine or StatisticsEngine()

    def profile(self, dataframe: pd.DataFrame) -> DatasetProfile:
        """Generate a dataset profile.

        Args:
            dataframe: Input pandas DataFrame.

        Returns:
            DatasetProfile containing dataset metadata and statistics.
        """
        return DatasetProfile(
            summary=self._build_summary(dataframe),
            columns=self._build_column_profiles(dataframe),
            missing=self._build_missing_summary(dataframe),
            duplicates=self._build_duplicate_summary(dataframe),
        )

    def _build_summary(self, dataframe: pd.DataFrame) -> DatasetSummary:
        """Build dataset summary."""
        memory_usage = int(dataframe.memory_usage(deep=True).sum())
        return DatasetSummary(
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            memory_usage_bytes=memory_usage,
        )

    def _build_column_profiles(self, dataframe: pd.DataFrame) -> list[ColumnProfile]:
        """Build metadata for every column."""
        profiles: list[ColumnProfile] = []
        row_count = len(dataframe)

        for column in dataframe.columns:
            series = dataframe[column]
            missing = int(series.isna().sum())
            percentage = 0.0 if row_count == 0 else (missing / row_count) * 100

            num_stats = self._stats_engine.compute(series)

            info = BasicColumnInfo(
                name=str(column),
                dtype=str(series.dtype),
                missing_count=missing,
                missing_percentage=percentage,
                unique_count=int(series.nunique(dropna=True)),
            )

            profiles.append(
                ColumnProfile(
                    info=info,
                    numeric=num_stats,
                )
            )

        return profiles

    def _build_missing_summary(self, dataframe: pd.DataFrame) -> MissingValueSummary:
        """Build dataset missing-value summary."""
        missing_per_column = dataframe.isna().sum()
        return MissingValueSummary(
            total_missing_values=int(missing_per_column.sum()),
            columns_with_missing=int((missing_per_column > 0).sum()),
        )

    def _build_duplicate_summary(self, dataframe: pd.DataFrame) -> DuplicateSummary:
        """Build duplicate-row summary."""
        duplicates = int(dataframe.duplicated().sum())
        return DuplicateSummary(
            duplicate_rows=duplicates,
        )