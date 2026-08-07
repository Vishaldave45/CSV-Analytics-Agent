import pytest
from pydantic import ValidationError

from csv_analytics_agent.profiler.models import (
    CategoricalStatistics,
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DatetimeStatistics,
    DuplicateSummary,
    MissingSummary,
    NumericStatistics,
)


def test_numeric_statistics_defaults() -> None:
    stats = NumericStatistics()
    assert stats.mean is None
    assert stats.median is None
    assert stats.std is None
    assert stats.variance is None
    assert stats.min is None
    assert stats.max is None
    assert stats.q1 is None
    assert stats.q3 is None


def test_numeric_statistics_custom_values() -> None:
    stats = NumericStatistics(
        mean=25.5,
        median=24.0,
        std=5.1,
        variance=26.01,
        min=10.0,
        max=50.0,
        q1=20.0,
        q3=30.0,
    )
    assert stats.mean == 25.5
    assert stats.median == 24.0
    assert stats.min == 10.0
    assert stats.max == 50.0


def test_categorical_statistics_valid() -> None:
    stats = CategoricalStatistics(
        mode="Ahmedabad",
        frequency=150,
        category_count=4,
    )
    assert stats.mode == "Ahmedabad"
    assert stats.frequency == 150
    assert stats.category_count == 4


def test_categorical_statistics_negative_counts() -> None:
    invalid_count = int("-1")
    with pytest.raises(ValidationError):
        CategoricalStatistics(category_count=invalid_count)


def test_datetime_statistics_valid() -> None:
    stats = DatetimeStatistics(
        earliest="2026-01-01T00:00:00",
        latest="2026-12-31T23:59:59",
    )
    assert stats.earliest == "2026-01-01T00:00:00"
    assert stats.latest == "2026-12-31T23:59:59"


def test_column_profile_valid() -> None:
    info_num = NumericStatistics(mean=50.0)
    profile = ColumnProfile(
        name="age",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
        numeric=info_num,
    )
    assert profile.name == "age"
    assert profile.dtype == "int64"
    assert profile.missing_count == 0
    assert profile.missing_percentage == 0.0
    assert profile.unique_count == 100
    assert profile.numeric is not None
    assert profile.numeric.mean == 50.0
    assert profile.categorical is None
    assert profile.datetime is None


def test_column_profile_percentage_validation() -> None:
    invalid_pct = float("105.0")
    with pytest.raises(ValidationError):
        ColumnProfile(
            name="col",
            dtype="float64",
            missing_count=10,
            missing_percentage=invalid_pct,
            unique_count=5,
        )


def test_model_immutability() -> None:
    summary = DatasetSummary(row_count=100, column_count=5, memory_usage_bytes=1024)
    with pytest.raises(ValidationError):
        summary.row_count = 200  # type: ignore[misc]


def test_dataset_profile_nested() -> None:
    summary = DatasetSummary(row_count=10, column_count=1, memory_usage_bytes=200)
    col = ColumnProfile(
        name="id",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=10,
    )
    missing = MissingSummary(total_missing_values=0, columns_with_missing=0)
    duplicates = DuplicateSummary(duplicate_rows=0)

    profile = DatasetProfile(
        summary=summary,
        columns=[col],
        missing=missing,
        duplicates=duplicates,
    )

    assert profile.summary.row_count == 10
    assert len(profile.columns) == 1
    assert profile.columns[0].name == "id"
