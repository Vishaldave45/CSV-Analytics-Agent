# ADR-002: Immutable Data Models for Profiler and Insights

## Status
Accepted

## Context
Data payloads passing through the profiling and insight generation pipeline must remain constant across module boundaries to prevent transient mutations or side effects in downstream tools.

## Decision
Implement all domain models in `profiler/models.py` and `insights/models.py` using Pydantic v2 `BaseModel` with `model_config = ConfigDict(frozen=True)`.

## Consequences
* Immutability guarantees across all component boundaries.
* Automatic Pydantic validation on attributes.
* Native JSON serialization (`.model_dump()`, `.model_dump_json()`) for LLM prompt context formatting.
