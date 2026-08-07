"""Unit tests for Phase 6 AnalyticsEngine."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.exceptions import EngineValidationError
from csv_analytics_agent.execution.models import (
    ExecutionRequest,
    ExecutionStatus,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "score": [85.0, 92.0, 78.0, 95.0],
            "grade": ["B", "A", "C", "A"],
        }
    )


def test_analytics_engine_capabilities() -> None:
    engine = AnalyticsEngine()
    caps = engine.list_capabilities()
    cap_names = [c.name for c in caps]
    assert "aggregate" in cap_names
    assert "filter" in cap_names
    assert "group" in cap_names
    assert "sort" in cap_names
    assert "top_n" in cap_names


def test_analytics_engine_execute_aggregate(sample_df: pd.DataFrame) -> None:
    engine = AnalyticsEngine()
    req = ExecutionRequest(
        capability_name="aggregate",
        target_columns=["score"],
        parameters={"operation": "mean"},
    )
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data == 87.5


def test_analytics_engine_invalid_capability(sample_df: pd.DataFrame) -> None:
    engine = AnalyticsEngine()
    req = ExecutionRequest(capability_name="unsupported_capability")
    with pytest.raises(EngineValidationError):
        engine.execute_capability(req, sample_df)
