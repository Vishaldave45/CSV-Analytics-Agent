"""Unit tests for Phase 4 CapabilityRegistry."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.base import BaseEngine
from csv_analytics_agent.execution.exceptions import CapabilityNotFoundError
from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    EngineMetadata,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from csv_analytics_agent.execution.registry import CapabilityRegistry


class DummyEngine(BaseEngine):
    """Dummy engine implementation for testing registry functionality."""

    @property
    def metadata(self) -> EngineMetadata:
        return EngineMetadata(name="dummy", supported_capabilities=["aggregate"])

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return [
            CapabilityDescriptor(
                name="aggregate",
                description="Aggregates values.",
                provider_name="dummy_provider",
            )
        ]

    def execute_capability(
        self,
        request: ExecutionRequest,
        df: pd.DataFrame,
    ) -> ExecutionResult:
        return ExecutionResult(
            capability_name=request.capability_name,
            status=ExecutionStatus.SUCCESS,
            message="Dummy executed.",
            data=42.0,
        )


def test_registry_registration_and_lookup() -> None:
    registry = CapabilityRegistry()
    engine = DummyEngine()
    desc = engine.list_capabilities()[0]

    registry.register(desc, engine, priority=5)

    assert "aggregate" in registry.list_capabilities()

    reg = registry.get("aggregate")
    assert reg.descriptor.name == "aggregate"
    assert reg.priority == 5
    assert registry.get_engine("aggregate") == engine


def test_registry_discover() -> None:
    registry = CapabilityRegistry()
    engine = DummyEngine()
    desc = engine.list_capabilities()[0]

    registry.register(desc, engine)

    discovered = registry.discover()
    assert len(discovered) == 1
    assert discovered[0].name == "aggregate"

    filtered = registry.discover("non_existent")
    assert len(filtered) == 0


def test_registry_export_llm_schema() -> None:
    registry = CapabilityRegistry()
    engine = DummyEngine()
    desc = engine.list_capabilities()[0]

    registry.register(desc, engine)

    schemas = registry.export_llm_schema()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "aggregate"


def test_registry_unregister() -> None:
    registry = CapabilityRegistry()
    engine = DummyEngine()
    desc = engine.list_capabilities()[0]

    registry.register(desc, engine)
    registry.unregister("aggregate")

    assert "aggregate" not in registry.list_capabilities()
    with pytest.raises(CapabilityNotFoundError):
        registry.get("aggregate")
