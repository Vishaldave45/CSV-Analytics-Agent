"""Unit tests for Phase 1 execution domain models."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    CapabilityRegistration,
    EngineMetadata,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ProviderMetadata,
)


def test_execution_status_enum() -> None:
    """Verify ExecutionStatus enum values."""
    assert ExecutionStatus.SUCCESS.value == "success"
    assert ExecutionStatus.FAILED.value == "failed"
    assert ExecutionStatus.CANCELLED.value == "cancelled"


def test_provider_metadata_valid() -> None:
    """Test valid ProviderMetadata creation and immutability."""
    provider = ProviderMetadata(
        name="pandas",
        version="1.0.0",
        description="Pandas in-memory execution provider.",
    )
    assert provider.name == "pandas"
    assert provider.version == "1.0.0"

    with pytest.raises(ValidationError):
        setattr(provider, "name", "new_name")  # noqa: B010


def test_engine_metadata_valid() -> None:
    """Test valid EngineMetadata creation."""
    engine = EngineMetadata(
        name="analytics",
        version="1.0.0",
        supported_capabilities=["aggregate", "filter"],
    )
    assert engine.name == "analytics"
    assert "aggregate" in engine.supported_capabilities


def test_capability_descriptor_valid() -> None:
    """Test valid CapabilityDescriptor creation and field validation."""
    desc = CapabilityDescriptor(
        name="aggregate",
        description="Calculates columnar aggregations.",
        parameters_schema={"type": "object", "properties": {"operation": {"type": "string"}}},
        provider_name="pandas",
    )
    assert desc.name == "aggregate"
    assert desc.provider_name == "pandas"


def test_execution_request_valid() -> None:
    """Test ExecutionRequest creation and frozen immutability."""
    req = ExecutionRequest(
        capability_name="aggregate",
        target_columns=["salary"],
        parameters={"operation": "mean"},
    )
    assert req.capability_name == "aggregate"
    assert req.target_columns == ["salary"]
    assert req.parameters["operation"] == "mean"

    with pytest.raises(ValidationError):
        setattr(req, "capability_name", "new_cap")  # noqa: B010


def test_execution_result_valid() -> None:
    """Test ExecutionResult creation and status assignment."""
    res: ExecutionResult = ExecutionResult(
        capability_name="aggregate",
        status=ExecutionStatus.SUCCESS,
        message="Aggregated mean successfully.",
        data=65000.5,
        execution_time_ms=1.45,
    )
    assert res.capability_name == "aggregate"
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data == 65000.5
    assert res.execution_time_ms == 1.45


def test_execution_result_is_picklable() -> None:
    """Regression test ensuring ExecutionResult is cleanly picklable across data payload types."""
    import pickle

    # 1. Dict payload
    res_dict = ExecutionResult(
        capability_name="test_dict",
        status=ExecutionStatus.SUCCESS,
        message="ok",
        data={"key": "value", "nested": [1, 2, 3]},
    )
    restored_dict = pickle.loads(pickle.dumps(res_dict))
    assert restored_dict == res_dict

    # 2. Float payload
    res_num = ExecutionResult(
        capability_name="aggregate",
        status=ExecutionStatus.SUCCESS,
        message="ok",
        data=42.5,
        execution_time_ms=10.2,
    )
    restored_num = pickle.loads(pickle.dumps(res_num))
    assert restored_num == res_num

    # 3. VisualizationPlan payload
    from csv_analytics_agent.visualization.models import (
        Axis,
        ChartSpecification,
        ChartType,
        VisualizationPlan,
    )

    spec = ChartSpecification(
        chart_type=ChartType.BOXPLOT,
        title="Distribution of Age",
        x_axis=Axis(column="age"),
        description="Distribution of Age boxplot",
    )
    plan = VisualizationPlan(primary=spec, alternatives=[])
    res_plan = ExecutionResult(
        capability_name="recommend_visualization",
        status=ExecutionStatus.SUCCESS,
        message="Generated plan",
        data=plan,
    )
    restored_plan = pickle.loads(pickle.dumps(res_plan))
    assert restored_plan == res_plan

    # 4. Bytes payload (e.g. rendered chart PNG bytes)
    res_bytes = ExecutionResult(
        capability_name="render_visualization",
        status=ExecutionStatus.SUCCESS,
        message="Rendered chart",
        data=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
    )
    restored_bytes = pickle.loads(pickle.dumps(res_bytes))
    assert restored_bytes == res_bytes

    # 5. None payload (e.g. on failure)
    res_none = ExecutionResult(
        capability_name="failed_cap",
        status=ExecutionStatus.FAILED,
        message="something broke",
        data=None,
    )
    restored_none = pickle.loads(pickle.dumps(res_none))
    assert restored_none == res_none


def test_capability_registration_valid() -> None:
    """Test CapabilityRegistration model container."""
    desc = CapabilityDescriptor(
        name="filter",
        description="Filters DataFrame rows.",
        provider_name="pandas",
    )
    reg = CapabilityRegistration(descriptor=desc, priority=10)
    assert reg.descriptor.name == "filter"
    assert reg.priority == 10
