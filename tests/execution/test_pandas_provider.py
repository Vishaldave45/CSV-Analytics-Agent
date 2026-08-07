"""Unit tests for Phase 5 PandasProvider."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.exceptions import ProviderError
from csv_analytics_agent.execution.models import (
    ExecutionRequest,
    ExecutionStatus,
)
from csv_analytics_agent.execution.providers.pandas import PandasProvider


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "department": ["HR", "IT", "IT", "HR", "Sales"],
            "salary": [50000.0, 60000.0, 75000.0, 90000.0, 110000.0],
            "age": [25, 30, 35, 40, 45],
        }
    )


def test_pandas_provider_supports(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    assert provider.supports("aggregate") is True
    assert provider.supports("filter") is True
    assert provider.supports("unsupported_cap") is False


def test_pandas_provider_aggregate_mean(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="aggregate",
        target_columns=["salary"],
        parameters={"operation": "mean"},
    )
    res = provider.execute(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data == 77000.0


def test_pandas_provider_filter_gt(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="filter",
        target_columns=["salary"],
        parameters={"operator": "gt", "value": 70000.0},
    )
    res = provider.execute(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, pd.DataFrame)
    assert len(res.data) == 3


def test_pandas_provider_group_mean(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="group",
        target_columns=["salary"],
        parameters={"by": "department", "operation": "mean"},
    )
    res = provider.execute(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, dict)
    assert res.data["IT"] == 67500.0


def test_pandas_provider_sort(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="sort",
        target_columns=["salary"],
        parameters={"order": "desc"},
    )
    res = provider.execute(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, pd.DataFrame)
    assert res.data.iloc[0]["name"] == "Eve"


def test_pandas_provider_top_n(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="top_n",
        target_columns=["salary"],
        parameters={"n": 2, "order": "desc"},
    )
    res = provider.execute(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert len(res.data) == 2


def test_pandas_provider_missing_column_raises_error(sample_df: pd.DataFrame) -> None:
    provider = PandasProvider()
    req = ExecutionRequest(
        capability_name="aggregate",
        target_columns=["invalid_column"],
    )
    with pytest.raises(ProviderError):
        provider.execute(req, sample_df)
