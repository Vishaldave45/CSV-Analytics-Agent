"""Unified canonical UI response model for the CSV Analytics Agent."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.results.models import AnalysisArtifact


class AgentResponseType(str, Enum):
    """Classification of the primary response content type."""

    TEXT = "text"
    SCALAR = "scalar"
    TABLE = "table"
    CHART = "chart"
    TABLE_AND_CHART = "table_and_chart"
    ERROR = "error"
    CLARIFICATION = "clarification"


class AgentResponse(BaseModel):
    """Canonical user-facing response contract for Streamlit UI rendering.

    This model completely encapsulates all analytical outputs, stripping
    away LangGraph tool execution logs, trace IDs, and intermediate payloads.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    type: AgentResponseType = Field(
        default=AgentResponseType.TEXT,
        description="The primary presentation mode for the UI.",
    )
    answer: str = Field(
        default="",
        description="The concise, natural-language explanation or answer.",
    )
    table: AnalysisArtifact | None = Field(
        default=None,
        description="The primary data table or scalar artifact, if applicable.",
    )
    visualization: AnalysisArtifact | None = Field(
        default=None,
        description="The primary chart or interactive diagram artifact, if applicable.",
    )
    artifacts: list[AnalysisArtifact] = Field(
        default_factory=list,
        description="List of all analytical output artifacts (tables, charts, images, etc.).",
    )
    insights: list[str] = Field(
        default_factory=list,
        description="Optional list of concise insights or observations.",
    )
    calculation: str | None = Field(
        default=None,
        description="Optional metadata string explaining how the answer was computed.",
    )
    error: str | None = Field(
        default=None,
        description="Safe, user-facing error message (no stack traces).",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Optional suggested follow-up questions.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Internal metadata (e.g. executed tools, node times) for debug views only.",
    )


__all__ = [
    "AgentResponse",
    "AgentResponseType",
]
