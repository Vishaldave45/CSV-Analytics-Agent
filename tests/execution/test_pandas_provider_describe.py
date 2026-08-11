"""Tests for the pandas execution provider describe capability bug fix."""

import pandas as pd

from csv_analytics_agent.execution.models import ExecutionRequest
from csv_analytics_agent.execution.providers.pandas import PandasProvider
from csv_analytics_agent.profiler.profiler import DatasetProfiler


def test_pandas_provider_describe_with_dict_profile() -> None:
    """Verify describe capability works when request context profile is a dict instead of a model."""
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})

    # Simulate LangGraph state serialization by turning profile into a dict
    profile = DatasetProfiler().profile(df)
    profile_dict = profile.model_dump()

    request = ExecutionRequest(
        capability_name="describe",
        target_columns=[],
        parameters={},
        context_metadata={"profile": profile_dict},
    )

    provider = PandasProvider()

    # Should not raise AttributeError: 'dict' object has no attribute 'columns'
    result = provider.execute(request, df)

    assert result.status.value == "success"
    assert "summary" in result.data
    assert "columns" in result.data
    assert len(result.data["columns"]) == 2
