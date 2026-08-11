"""Domain models for Stage 5 Execution Engine Framework.

This module defines immutable Pydantic v2 domain models representing execution requests,
results, descriptors, engine metadata, provider metadata, and registrations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Execution outcome status state."""

    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderMetadata(BaseModel):
    """Metadata describing an execution provider.

    Attributes:
        name: Programmatic identifier of the provider.
        version: Semantic version string.
        description: Human-readable provider description.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Programmatic name of provider.")
    version: str = Field(default="1.0.0", description="Semantic version string.")
    description: str = Field(..., min_length=1, description="Provider description.")


class EngineMetadata(BaseModel):
    """Metadata describing a domain engine.

    Attributes:
        name: Programmatic identifier of the domain engine.
        version: Semantic version string.
        supported_capabilities: List of capability names handled by this engine.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Programmatic name of engine.")
    version: str = Field(default="1.0.0", description="Semantic version string.")
    supported_capabilities: list[str] = Field(
        default_factory=list,
        description="Supported capability names.",
    )


class CapabilityDescriptor(BaseModel):
    """Descriptor defining a registered capability for discovery and LLM schema generation.

    Attributes:
        name: Unique programmatic identifier of the capability (e.g. 'aggregate').
        description: Human and LLM-readable purpose description.
        parameters_schema: OpenAPI/JSON schema dictionary defining valid arguments.
        provider_name: Default bound provider name.
        preferred_execution_engine: Engine preference for deterministic planning.
        fallback_execution_engine: Engine fallback when preferred execution is insufficient.
        output_contract: Optional output contract describing the expected payload type.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Unique capability identifier.")
    description: str = Field(..., min_length=1, description="Human/LLM capability description.")
    parameters_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema defining parameters.",
    )
    provider_name: str = Field(..., min_length=1, description="Bound provider name.")
    preferred_execution_engine: str | None = Field(
        default=None,
        description="Preferred execution engine for this capability.",
    )
    fallback_execution_engine: str | None = Field(
        default=None,
        description="Fallback execution engine if preferred engine is insufficient.",
    )
    output_contract: dict[str, Any] | None = Field(
        default=None,
        description="Optional expected output contract describing payload structure.",
    )


class ExecutionRequest(BaseModel):
    """Unified payload requesting execution of a specific capability.

    Attributes:
        capability_name: Target capability name to invoke.
        target_columns: Target column names for execution.
        parameters: Arbitrary parameter dictionary.
        context_metadata: Additional execution pipeline metadata.
    """

    model_config = ConfigDict(frozen=True)

    capability_name: str = Field(..., min_length=1, description="Target capability name.")
    target_columns: list[str] = Field(
        default_factory=list,
        description="Target column names.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution parameters dictionary.",
    )
    context_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline context metadata.",
    )


class ExecutionResult(BaseModel):
    """Unified result payload returned by engines and providers.

    Attributes:
        capability_name: Capability name executed.
        status: Execution status outcome.
        message: Execution log message or error description.
        data: Execution result payload data.
        execution_time_ms: Duration in milliseconds.
        metadata: Result metadata.
    """

    model_config = ConfigDict(frozen=True)

    capability_name: str = Field(..., min_length=1, description="Capability name executed.")
    status: ExecutionStatus = Field(..., description="Execution status outcome.")
    message: str = Field(..., min_length=1, description="Execution message details.")
    data: Any | None = Field(default=None, description="Result payload data.")
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration in milliseconds.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution result metadata.",
    )


class CapabilityRegistration(BaseModel):
    """Container holding a registered capability descriptor and associated metadata.

    Attributes:
        descriptor: Capability descriptor metadata.
        priority: Priority order rank (higher priority preferred).
        metadata: Registration metadata.
    """

    model_config = ConfigDict(frozen=True)

    descriptor: CapabilityDescriptor = Field(..., description="Registered capability descriptor.")
    priority: int = Field(default=0, ge=0, description="Priority ordering rank.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Registration metadata.",
    )


__all__ = [
    "CapabilityDescriptor",
    "CapabilityRegistration",
    "EngineMetadata",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "ProviderMetadata",
]
