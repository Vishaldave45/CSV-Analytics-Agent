from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    """High-level information about a dataset."""

    row_count: int = Field(..., ge=0)
    column_count: int = Field(..., ge=0)
    memory_usage_bytes: int = Field(..., ge=0)


class ColumnProfile(BaseModel):
    """Metadata for a single column."""

    name: str
    dtype: str
    missing_count: int = Field(..., ge=0)
    missing_percentage: float = Field(..., ge=0.0, le=100.0)
    unique_count: int = Field(..., ge=0)


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