"""Unit tests for insights domain models and evidence structures."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)


def test_create_evidence() -> None:
    """Test creating a valid Evidence instance."""
    evidence = Evidence(
        column="salary",
        metric="missing_percentage",
        value=45.0,
        threshold=30.0,
    )

    assert evidence.column == "salary"
    assert evidence.metric == "missing_percentage"
    assert evidence.value == 45.0
    assert evidence.threshold == 30.0


def test_evidence_immutability() -> None:
    """Verify mutation on frozen Evidence model raises ValidationError."""
    evidence = Evidence(
        column="salary",
        metric="missing_percentage",
        value=45.0,
        threshold=30.0,
    )

    with pytest.raises(ValidationError):
        evidence.metric = "new_metric"  # type: ignore[misc]


def test_create_insight_with_evidence() -> None:
    """Test creating a valid Insight instance containing structured Evidence list."""
    evidence = Evidence(
        column="age",
        metric="missing_percentage",
        value=45.0,
        threshold=30.0,
    )
    insight = Insight(
        category=InsightCategory.DATA_QUALITY,
        severity=Severity.HIGH,
        title="High missing rate in age",
        description="The age column contains 45% missing values.",
        recommendation="Consider imputing missing values or dropping column if unneeded.",
        evidence=[evidence],
    )

    assert insight.category == InsightCategory.DATA_QUALITY
    assert insight.severity == Severity.HIGH
    assert insight.title == "High missing rate in age"
    assert insight.description == "The age column contains 45% missing values."
    assert (
        insight.recommendation
        == "Consider imputing missing values or dropping column if unneeded."
    )
    assert len(insight.evidence) == 1
    assert insight.evidence[0].column == "age"
    assert insight.evidence[0].metric == "missing_percentage"
    assert insight.evidence[0].value == 45.0


def test_insight_is_immutable() -> None:
    """Verify mutation on frozen model raises ValidationError."""
    insight = Insight(
        category=InsightCategory.GENERAL,
        severity=Severity.INFO,
        title="Summary profile",
        description="Dataset contains 100 rows.",
        recommendation="Proceed with standard analysis.",
    )

    with pytest.raises(ValidationError):
        insight.title = "Modified title"  # type: ignore[misc]


def test_empty_title_validation() -> None:
    """Test validation fails when title is empty string."""
    with pytest.raises(ValidationError):
        Insight(
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="",
            description="Empty title provided.",
            recommendation="Provide non-empty title.",
        )


def test_empty_description_validation() -> None:
    """Test validation fails when description is empty string."""
    with pytest.raises(ValidationError):
        Insight(
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="Valid Title",
            description="",
            recommendation="Provide non-empty description.",
        )


def test_empty_recommendation_validation() -> None:
    """Test validation fails when recommendation is empty string."""
    with pytest.raises(ValidationError):
        Insight(
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="Valid Title",
            description="Valid Description",
            recommendation="",
        )


def test_invalid_enum_values() -> None:
    """Test validation fails with invalid category or severity enum string."""
    with pytest.raises(ValidationError):
        Insight(
            category="invalid_category",  # type: ignore[arg-type]
            severity=Severity.LOW,
            title="Title",
            description="Description",
            recommendation="Recommendation",
        )


def test_enum_values() -> None:
    """Verify Severity and InsightCategory enum string values."""
    assert Severity.HIGH.value == "high"
    assert Severity.INFO.value == "info"
    assert InsightCategory.DATA_QUALITY.value == "data_quality"
    assert InsightCategory.CARDINALITY.value == "cardinality"
