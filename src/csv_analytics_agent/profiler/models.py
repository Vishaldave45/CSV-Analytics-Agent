"""Pydantic data models for dataset profiling."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NumericStatistics(BaseModel):
    """Statistical metrics for numeric columns."""

    model_config = ConfigDict(frozen=True)

    mean: float | None = None
    median: float | None = None
    std: float | None = None
    variance: float | None = None
    min: float | None = None
    max: float | None = None
    q1: float | None = None
    q3: float | None = None


class CategoricalStatistics(BaseModel):
    """Statistical metrics for categorical columns."""

    model_config = ConfigDict(frozen=True)

    mode: str | None = None
    frequency: int | None = Field(default=None, ge=0)
    category_count: int = Field(default=0, ge=0)


class DatetimeStatistics(BaseModel):
    """Statistical metrics for datetime columns."""

    model_config = ConfigDict(frozen=True)

    earliest: str | None = None
    latest: str | None = None


class ColumnProfile(BaseModel):
    """Complete profile for an individual dataset column."""

    model_config = ConfigDict(frozen=True)

    name: str
    dtype: str
    missing_count: int = Field(..., ge=0)
    missing_percentage: float = Field(..., ge=0.0, le=100.0)
    unique_count: int = Field(..., ge=0)
    numeric: NumericStatistics | None = None
    categorical: CategoricalStatistics | None = None
    datetime: DatetimeStatistics | None = None


class DatasetSummary(BaseModel):
    """High-level summary metadata for a dataset."""

    model_config = ConfigDict(frozen=True)

    row_count: int = Field(..., ge=0)
    column_count: int = Field(..., ge=0)
    memory_usage_bytes: int = Field(..., ge=0)


class MissingSummary(BaseModel):
    """Dataset-level missing value statistics."""

    model_config = ConfigDict(frozen=True)

    total_missing_values: int = Field(..., ge=0)
    columns_with_missing: int = Field(..., ge=0)


class DuplicateSummary(BaseModel):
    """Dataset-level duplicate row statistics."""

    model_config = ConfigDict(frozen=True)

    duplicate_rows: int = Field(..., ge=0)


class DatasetProfile(BaseModel):
    """Complete, immutable profile for a dataset."""

    model_config = ConfigDict(frozen=True)

    summary: DatasetSummary
    columns: list[ColumnProfile]
    missing: MissingSummary
    duplicates: DuplicateSummary
