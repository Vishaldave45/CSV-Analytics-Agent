"""Data models for dataset profiling."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BasicColumnInfo(BaseModel):
    """Basic metadata for a column."""

    name: str
    dtype: str
    missing_count: int = Field(..., ge=0)
    missing_percentage: float = Field(..., ge=0.0, le=100.0)
    unique_count: int = Field(..., ge=0)


class NumericStatistics(BaseModel):
    """Statistics for numeric columns."""

    mean: float | None = None
    median: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    standard_deviation: float | None = None
    variance: float | None = None
    q1: float | None = None
    q3: float | None = None


class CategoricalStatistics(BaseModel):
    """Statistics for categorical columns."""

    mode: str | None = None
    top_frequency: int | None = None
    category_count: int = Field(default=0, ge=0)


class DatetimeStatistics(BaseModel):
    """Statistics for datetime columns."""

    minimum: str | None = None
    maximum: str | None = None


class ColumnProfile(BaseModel):
    """Complete profile for one column."""

    info: BasicColumnInfo
    numeric: NumericStatistics | None = None
    categorical: CategoricalStatistics | None = None
    datetime: DatetimeStatistics | None = None


class DatasetSummary(BaseModel):
    """High-level information about a dataset."""

    row_count: int = Field(..., ge=0)
    column_count: int = Field(..., ge=0)
    memory_usage_bytes: int = Field(..., ge=0)


class MissingValueSummary(BaseModel):
    """Dataset-level missing value statistics."""

    total_missing_values: int = Field(..., ge=0)
    columns_with_missing: int = Field(..., ge=0)


class DuplicateSummary(BaseModel):
    """Duplicate row information."""

    duplicate_rows: int = Field(..., ge=0)


class DatasetProfile(BaseModel):
    """Complete dataset profile."""

    summary: DatasetSummary
    columns: list[ColumnProfile]
    missing: MissingValueSummary
    duplicates: DuplicateSummary