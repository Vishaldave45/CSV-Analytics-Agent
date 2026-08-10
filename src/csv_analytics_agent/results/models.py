"""Application-level AnalysisResult and AnalysisArtifact domain models."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.python_engine.models import PythonArtifactType


class AnalysisStatus(str, Enum):
    """Execution status classification for analysis results."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class AnalysisArtifact(BaseModel):
    """Application-level analytical output artifact model.

    Attributes:
        artifact_id: Persistent unique identifier string.
        artifact_type: PythonArtifactType classification enum.
        name: Short programmatic name key.
        mime_type: Optional MIME media type string.
        title: Optional human-readable display title.
        description: Optional textual description of the artifact.
        payload: Runtime object payload (DataFrame, Plotly figure, Bytes, etc.).
        metadata: Key-value dictionary containing metadata properties.
        downloadable: Flag indicating if artifact can be downloaded by user.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    artifact_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the artifact.",
    )
    artifact_type: PythonArtifactType = Field(
        ...,
        description="Type classification of the analytical artifact.",
    )
    name: str = Field(
        ...,
        description="Programmatic name identifier.",
    )
    mime_type: str | None = Field(
        default=None,
        description="Optional MIME type string.",
    )
    title: str | None = Field(
        default=None,
        description="Optional human-readable title.",
    )
    description: str | None = Field(
        default=None,
        description="Optional textual description of content.",
    )
    payload: Any = Field(
        default=None,
        description="Runtime payload object.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata dictionary.",
    )
    downloadable: bool = Field(
        default=False,
        description="Whether artifact is downloadable.",
    )


class AnalysisResult(BaseModel):
    """Unified application-level result payload for all analytical outputs.

    Attributes:
        status: AnalysisStatus classification (SUCCESS, PARTIAL, FAILED).
        narrative: Human-readable textual narrative or summary.
        artifacts: List of AnalysisArtifact objects.
        execution_time_ms: Execution duration in milliseconds.
        source: Source execution engine identifier string.
        question: Optional natural-language question.
        dataset_hash: Optional SHA-256 dataset hash string.
        metadata: Dictionary containing metadata properties.
        error_type: Optional error type string if status != SUCCESS.
        error_message: Optional error message string if status != SUCCESS.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    status: AnalysisStatus = Field(
        default=AnalysisStatus.SUCCESS,
        description="Execution outcome status.",
    )
    narrative: str = Field(
        default="",
        description="Human-readable text summary of analysis outcome.",
    )
    artifacts: list[AnalysisArtifact] = Field(
        default_factory=list,
        description="List of produced analytical output artifacts.",
    )
    execution_time_ms: float | None = Field(
        default=None,
        description="Execution time in milliseconds.",
    )
    source: str = Field(
        default="unknown",
        description="Engine source identifier ('deterministic_engine', 'python_engine', 'unknown').",
    )
    question: str | None = Field(
        default=None,
        description="Target question query string.",
    )
    dataset_hash: str | None = Field(
        default=None,
        description="Dataset SHA-256 hash string.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Result metadata dictionary.",
    )
    error_type: str | None = Field(
        default=None,
        description="Error type string if execution failed or was partial.",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message string if execution failed or was partial.",
    )

    @classmethod
    def failure(
        cls,
        error_type: str,
        error_message: str,
        source: str = "unknown",
        question: str | None = None,
        dataset_hash: str | None = None,
        execution_time_ms: float | None = None,
    ) -> AnalysisResult:
        """Construct a failed AnalysisResult instance."""
        return cls(
            status=AnalysisStatus.FAILED,
            narrative=error_message,
            artifacts=[],
            execution_time_ms=execution_time_ms,
            source=source,
            question=question,
            dataset_hash=dataset_hash,
            error_type=error_type,
            error_message=error_message,
        )

    @classmethod
    def partial(
        cls,
        artifacts: list[AnalysisArtifact],
        error_type: str | None = None,
        error_message: str | None = None,
        narrative: str = "",
        source: str = "unknown",
        question: str | None = None,
        dataset_hash: str | None = None,
        execution_time_ms: float | None = None,
    ) -> AnalysisResult:
        """Construct a partial AnalysisResult instance with available artifacts."""
        return cls(
            status=AnalysisStatus.PARTIAL,
            narrative=narrative or error_message or "Analysis completed partially.",
            artifacts=artifacts,
            execution_time_ms=execution_time_ms,
            source=source,
            question=question,
            dataset_hash=dataset_hash,
            error_type=error_type,
            error_message=error_message,
        )

    def merge(self, other: AnalysisResult) -> AnalysisResult:
        """Merge another AnalysisResult into a combined AnalysisResult instance.

        Args:
            other: Secondary AnalysisResult instance to merge.

        Returns:
            New combined AnalysisResult instance preserving artifact IDs and evaluating status.
        """
        combined_artifacts = list(self.artifacts) + list(other.artifacts)

        # Evaluate combined status
        if self.status == AnalysisStatus.SUCCESS and other.status == AnalysisStatus.SUCCESS:
            merged_status = AnalysisStatus.SUCCESS
        elif self.status == AnalysisStatus.FAILED and other.status == AnalysisStatus.FAILED:
            merged_status = AnalysisStatus.FAILED
        else:
            merged_status = AnalysisStatus.PARTIAL if combined_artifacts else AnalysisStatus.FAILED

        # Combine narratives
        narratives = [n for n in (self.narrative, other.narrative) if n.strip()]
        merged_narrative = "\n\n".join(narratives)

        # Combine metadata
        merged_meta = dict(self.metadata)
        for k, v in other.metadata.items():
            if k not in merged_meta:
                merged_meta[k] = v
            else:
                merged_meta[f"other_{k}"] = v

        # Combine execution time
        t1 = self.execution_time_ms or 0.0
        t2 = other.execution_time_ms or 0.0
        merged_time = (t1 + t2) if (self.execution_time_ms or other.execution_time_ms) else None

        return AnalysisResult(
            status=merged_status,
            narrative=merged_narrative,
            artifacts=combined_artifacts,
            execution_time_ms=merged_time,
            source=f"{self.source}+{other.source}",
            question=self.question or other.question,
            dataset_hash=self.dataset_hash or other.dataset_hash,
            metadata=merged_meta,
            error_type=self.error_type or other.error_type,
            error_message=self.error_message or other.error_message,
        )


__all__ = [
    "AnalysisArtifact",
    "AnalysisResult",
    "AnalysisStatus",
]
