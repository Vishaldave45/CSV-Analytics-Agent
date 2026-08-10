"""Graph-level domain models shared across LangGraph nodes.

This module re-exports PlannerResult so it can be referenced by AgentState
without depending on the (now-removed) planner/ subsystem.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.execution.models import ExecutionRequest


class PlannerResult(BaseModel):
    """Result payload produced by a planner node containing execution request and trace metadata.

    Used by AgentState to carry planning context across graph nodes.

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


__all__ = ["PlannerResult"]
