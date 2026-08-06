import pytest
from pydantic import ValidationError

from csv_analytics_agent.profiler.models import (
    BasicColumnInfo,
    CategoricalStatistics,
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DatetimeStatistics,
    DuplicateSummary,
    MissingValueSummary,
    NumericStatistics,
)


def test_dataset_summary_valid() -> None:
    summary = DatasetSummary(
        row_count=100,
        column_count=5,
        memory_usage_bytes=1024,
    )
    assert summary.row_count == 100
    assert summary.column_count == 5
    assert summary.memory_usage_bytes == 1024


def test_negative_row_count_raises() -> None:
    invalid_row_count = int("-1")
    with pytest.raises(ValidationError):
        DatasetSummary(
            row_count=invalid_row_count,
            column_count=5,
            memory_usage_bytes=1024,
        )


def test_basic_column_info_valid() -> None:
    info = BasicColumnInfo(
        name="age",
        dtype="int64",
        missing_count=2,
        missing_percentage=2.0,
        unique_count=50,
    )
    assert info.name == "age"
    assert info.dtype == "int64"
    assert info.missing_count == 2
    assert info.missing_percentage == 2.0
    assert info.unique_count == 50


def test_numeric_statistics_valid() -> None:
    stats = NumericStatistics(
        mean=25.0,
        median=24.5,
        minimum=10.0,
        maximum=50.0,
        standard_deviation=5.0,
        variance=25.0,
        q1=20.0,
        q3=30.0,
    )
    assert stats.mean == 25.0
    assert stats.median == 24.5
    assert stats.q1 == 20.0


def test_categorical_statistics_valid() -> None:
    cat = CategoricalStatistics(
        mode="New York",
        top_frequency=15,
        category_count=5,
    )
    assert cat.mode == "New York"
    assert cat.top_frequency == 15
    assert cat.category_count == 5


def test_datetime_statistics_valid() -> None:
    dt = DatetimeStatistics(
        minimum="2026-01-01T00:00:00",
        maximum="2026-12-31T23:59:59",
    )
    assert dt.minimum == "2026-01-01T00:00:00"
    assert dt.maximum == "2026-12-31T23:59:59"


def test_column_profile_composition() -> None:
    info = BasicColumnInfo(
        name="salary",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
    )
    num_stats = NumericStatistics(mean=50000.0, median=48000.0)

    profile = ColumnProfile(
        info=info,
        numeric=num_stats,
    )

    assert profile.info.name == "salary"
    assert profile.numeric is not None
    assert profile.numeric.mean == 50000.0
    assert profile.categorical is None
    assert profile.datetime is None


def test_missing_value_summary_valid() -> None:
    missing = MissingValueSummary(
        total_missing_values=10,
        columns_with_missing=2,
    )
    assert missing.total_missing_values == 10
    assert missing.columns_with_missing == 2


def test_duplicate_summary_valid() -> None:
    dup = DuplicateSummary(duplicate_rows=5)
    assert dup.duplicate_rows == 5


def test_dataset_profile_valid() -> None:
    summary = DatasetSummary(row_count=100, column_count=1, memory_usage_bytes=500)
    info = BasicColumnInfo(
        name="id",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
    )
    col = ColumnProfile(info=info)
    missing = MissingValueSummary(total_missing_values=0, columns_with_missing=0)
    duplicates = DuplicateSummary(duplicate_rows=0)

    profile = DatasetProfile(
        summary=summary,
        columns=[col],
        missing=missing,
        duplicates=duplicates,
    )

    assert profile.summary.row_count == 100
    assert len(profile.columns) == 1
    assert profile.columns[0].info.name == "id"