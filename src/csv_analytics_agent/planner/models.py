"""Domain models for Stage 6 Deterministic Rule-Based Planner Engine.

This module defines immutable Pydantic v2 models representing parsed intents, parameters,
planner metadata, confidence scores, and reasoning trace logs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.execution.models import ExecutionRequest


class IntentType(str, Enum):
    """Broad analytical intent classification types."""

    AGGREGATE = "aggregate"
    FILTER = "filter"
    GROUP = "group"
    SORT = "sort"
    TOP_N = "top_n"
    UNKNOWN = "unknown"


class Parameter(BaseModel):
    """Extracted parameter definition from natural language text.

    Attributes:
        name: Parameter key name.
        value: Extracted typed parameter value.
        raw_text: Raw text snippet from query.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Parameter key name.")
    value: Any = Field(..., description="Typed parameter value.")
    raw_text: str = Field(default="", description="Raw query text snippet.")


class ParsedIntent(BaseModel):
    """Structured intent representation extracted from a natural language query.

    Attributes:
        intent_type: High-level analytical intent category.
        target_columns: Extracted dataset column names.
        parameters: Arbitrary key-value parameters dictionary.
        raw_query: Original natural language input question.
    """

    model_config = ConfigDict(frozen=True)

    intent_type: IntentType = Field(..., description="Extracted analytical intent category.")
    target_columns: list[str] = Field(
        default_factory=list,
        description="Target dataset column names.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted key-value parameters dictionary.",
    )
    raw_query: str = Field(..., min_length=1, description="Original natural language query.")


class PlannerMetadata(BaseModel):
    """Metadata describing a planner instance.

    Attributes:
        name: Programmatic identifier of the planner.
        version: Semantic version string.
        description: Human-readable description of planner mechanism.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Programmatic name of planner.")
    version: str = Field(default="1.0.0", description="Semantic version string.")
    description: str = Field(..., min_length=1, description="Planner description.")


class PlannerResult(BaseModel):
    """Result payload produced by the Planner containing execution request and trace metadata.

    Attributes:
        execution_request: Validated ExecutionRequest object if planning succeeded.
        confidence: Confidence score between 0.0 and 1.0.
        matched_rule: String description of matched rule/synonym pattern.
        reasoning_trace: Sequential list of human-readable decision steps.
        success: Whether planning successfully produced an ExecutionRequest.
        error_message: Optional error message if planning failed or was rejected.
    """

    model_config = ConfigDict(frozen=True)

    execution_request: ExecutionRequest | None = Field(
        default=None,
        description="Target ExecutionRequest payload.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )
    matched_rule: str | None = Field(
        default=None,
        description="Description of matched rule or pattern.",
    )
    reasoning_trace: list[str] = Field(
        default_factory=list,
        description="Sequential list of planning decision trace logs.",
    )
    success: bool = Field(..., description="Whether planning succeeded.")
    error_message: str | None = Field(
        default=None,
        description="Error description if planning failed.",
    )


__all__ = [
    "IntentType",
    "Parameter",
    "ParsedIntent",
    "PlannerMetadata",
    "PlannerResult",
]
