"""Bounded, checkpoint-safe representations for graph domain results.

Runtime artifacts deliberately live in :class:`RuntimeArtifactStore`; only their
small descriptive records cross the LangGraph checkpoint boundary.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypeAlias, TypedDict

from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class CheckpointArtifact(TypedDict):
    artifact_id: str
    artifact_type: str
    name: str
    mime_type: str | None
    title: str | None
    description: str | None
    metadata: dict[str, JSONValue]
    downloadable: bool


class AnalysisResultCheckpoint(TypedDict):
    status: str
    narrative: str
    artifacts: list[CheckpointArtifact]
    execution_time_ms: float | None
    source: str
    question: str | None
    dataset_hash: str | None
    metadata: dict[str, JSONValue]
    error_type: str | None
    error_message: str | None


class RuntimeArtifactStore:
    """Per-runtime store for payloads which must never enter checkpoint state."""

    def __init__(self) -> None:
        self._payloads: dict[str, object] = {}

    def put(self, artifact: AnalysisArtifact) -> None:
        self._payloads[artifact.artifact_id] = artifact.payload

    def get(self, artifact_id: str) -> object | None:
        return self._payloads.get(artifact_id)

    def clear(self) -> None:
        self._payloads.clear()


def json_safe(value: object, *, max_depth: int = 6) -> JSONValue:
    """Return a bounded JSON-compatible value without retaining arbitrary objects."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (str, int, bool)):
        return value
    if max_depth <= 0:
        return "<omitted: nested value>"
    if isinstance(value, Mapping):
        return {str(key): json_safe(item, max_depth=max_depth - 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item, max_depth=max_depth - 1) for item in list(value)[:100]]
    return f"<omitted: {type(value).__name__}>"


def json_object(value: object) -> dict[str, JSONValue]:
    """Convert mapping-like metadata to a checkpoint-safe JSON object."""
    safe = json_safe(value)
    return safe if isinstance(safe, dict) else {"value": safe}


def analysis_result_to_checkpoint(
    result: AnalysisResult, artifact_store: RuntimeArtifactStore
) -> AnalysisResultCheckpoint:
    """Split an application result into checkpoint metadata and runtime payloads."""
    artifacts: list[CheckpointArtifact] = []
    for artifact in result.artifacts:
        artifact_store.put(artifact)
        artifacts.append(
            {
                "artifact_id": artifact.artifact_id,
                "artifact_type": artifact.artifact_type.value,
                "name": artifact.name,
                "mime_type": artifact.mime_type,
                "title": artifact.title,
                "description": artifact.description,
                "metadata": json_object(artifact.metadata),
                "downloadable": artifact.downloadable,
            }
        )
    return {
        "status": result.status.value,
        "narrative": result.narrative,
        "artifacts": artifacts,
        "execution_time_ms": result.execution_time_ms,
        "source": result.source,
        "question": result.question,
        "dataset_hash": result.dataset_hash,
        "metadata": json_object(result.metadata),
        "error_type": result.error_type,
        "error_message": result.error_message,
    }


__all__ = [
    "AnalysisResultCheckpoint",
    "JSONValue",
    "RuntimeArtifactStore",
    "analysis_result_to_checkpoint",
    "json_object",
    "json_safe",
]
