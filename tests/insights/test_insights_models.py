"""Unit tests for insights domain models and evidence structures."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.insights.models import (
    ComparisonOperator,
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)


def test_create_evidence() -> None:
    """Test creating a valid Evidence instance."""
    evidence = Evidence(
        column_name="salary",
        metric_name="missing_percentage",
        observed_value=45.0,
        threshold=30.0,
        comparison=ComparisonOperator.GREATER_THAN_OR_EQUAL,
    )

    assert evidence.column_name == "salary"
    assert evidence.metric_name == "missing_percentage"
    assert evidence.observed_value == 45.0
    assert evidence.threshold == 30.0
    assert evidence.comparison == ComparisonOperator.GREATER_THAN_OR_EQUAL


def test_evidence_immutability() -> None:
    """Verify mutation on frozen Evidence model raises ValidationError."""
    evidence = Evidence(
        column_name="salary",
        metric_name="missing_percentage",
        observed_value=45.0,
        threshold=30.0,
        comparison=ComparisonOperator.GREATER_THAN_OR_EQUAL,
    )

    with pytest.raises(ValidationError):
        evidence.metric_name = "new_metric"  # type: ignore[misc]


def test_create_insight_with_evidence() -> None:
    """Test creating a valid Insight instance containing structured Evidence list."""
    evidence = Evidence(
        column_name="age",
        metric_name="missing_percentage",
        observed_value=45.0,
        threshold=30.0,
        comparison=ComparisonOperator.GREATER_THAN_OR_EQUAL,
    )
    insight = Insight(
        id="MISSING_HIGH",
        category=InsightCategory.DATA_QUALITY,
        severity=Severity.HIGH,
        title="High missing rate in age",
        description="The age column contains 45% missing values.",
        recommendation="Consider imputing missing values or dropping column if unneeded.",
        evidence=[evidence],
    )

    assert insight.id == "MISSING_HIGH"
    assert insight.category == InsightCategory.DATA_QUALITY
    assert insight.severity == Severity.HIGH
    assert insight.title == "High missing rate in age"
    assert insight.description == "The age column contains 45% missing values."
    assert (
        insight.recommendation
        == "Consider imputing missing values or dropping column if unneeded."
    )
    assert len(insight.evidence) == 1
    assert insight.evidence[0].column_name == "age"
    assert insight.evidence[0].comparison == ComparisonOperator.GREATER_THAN_OR_EQUAL


def test_insight_is_immutable() -> None:
    """Verify mutation on frozen model raises ValidationError."""
    insight = Insight(
        id="SUMMARY_PROFILE",
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
            id="TEST_ID",
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="",
            description="Empty title provided.",
            recommendation="Provide non-empty title.",
        )


def test_empty_id_validation() -> None:
    """Test validation fails when id is empty string."""
    with pytest.raises(ValidationError):
        Insight(
            id="",
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="Valid Title",
            description="Valid Description",
            recommendation="Valid Recommendation",
        )


def test_empty_description_validation() -> None:
    """Test validation fails when description is empty string."""
    with pytest.raises(ValidationError):
        Insight(
            id="TEST_ID",
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
            id="TEST_ID",
            category=InsightCategory.MISSING_VALUES,
            severity=Severity.MEDIUM,
            title="Valid Title",
            description="Valid Description",
            recommendation="",
        )


def test_invalid_enum_values() -> None:
    """Test validation fails with invalid category, severity, or operator enum string."""
    with pytest.raises(ValidationError):
        Insight(
            id="TEST_ID",
            category="invalid_category",  # type: ignore[arg-type]
            severity=Severity.LOW,
            title="Title",
            description="Description",
            recommendation="Recommendation",
        )

    with pytest.raises(ValidationError):
        Evidence(
            metric_name="missing",
            observed_value=10,
            comparison="INVALID_OP",  # type: ignore[arg-type]
        )


def test_enum_values() -> None:
    """Verify Severity, ComparisonOperator, and InsightCategory enum string values."""
    assert Severity.HIGH.value == "high"
    assert Severity.INFO.value == "info"
    assert InsightCategory.DATA_QUALITY.value == "data_quality"
    assert ComparisonOperator.GREATER_THAN_OR_EQUAL.value == ">="
    assert ComparisonOperator.EQUAL.value == "=="
