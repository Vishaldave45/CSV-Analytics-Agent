import pytest
from pydantic import ValidationError

from csv_analytics_agent.profiler.models import (
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingValueSummary,
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


def test_column_profile_valid() -> None:
    col = ColumnProfile(
        name="age",
        dtype="int64",
        missing_count=2,
        missing_percentage=2.0,
        unique_count=50,
    )
    assert col.name == "age"
    assert col.dtype == "int64"
    assert col.missing_count == 2
    assert col.missing_percentage == 2.0
    assert col.unique_count == 50


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
    col = ColumnProfile(
        name="id",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
    )
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
    assert profile.columns[0].name == "id"