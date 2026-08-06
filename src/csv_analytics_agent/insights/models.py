"""Domain models for the Insights Engine."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class InsightCategory(str, Enum):
    """Categories of generated insights."""

    GENERAL = "general"
    DATA_QUALITY = "data_quality"
    MISSING_VALUES = "missing_values"
    DUPLICATES = "duplicates"
    DISTRIBUTION = "distribution"
    OUTLIERS = "outliers"
    CARDINALITY = "cardinality"
    MEMORY = "memory"


class Severity(str, Enum):
    """Severity level of an insight."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Evidence(BaseModel):
    """Structured evidence backing a rule evaluation."""

    model_config = ConfigDict(frozen=True)

    column: str | None = Field(
        default=None,
        description="Target column associated with the evidence, if applicable.",
    )

    metric: str = Field(
        ...,
        min_length=1,
        description="Programmatic metric name (e.g. 'missing_percentage').",
    )

    value: float | int | str = Field(
        ...,
        description="Observed value of the metric.",
    )

    threshold: float | int | None = Field(
        default=None,
        description="Threshold value evaluated by the rule.",
    )


class Insight(BaseModel):
    """Represents a single deterministic insight backed by structured evidence."""

    model_config = ConfigDict(frozen=True)

    category: InsightCategory

    severity: Severity

    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        ...,
        min_length=1,
    )

    recommendation: str = Field(
        ...,
        min_length=1,
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Structured evidence items supporting the insight.",
    )