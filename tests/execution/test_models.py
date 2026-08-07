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


def test_execution_result_generic() -> None:
    """Test generic ExecutionResult creation and status assignment."""
    res: ExecutionResult[float] = ExecutionResult(
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
