# ADR-001: Layered Pipeline Architecture for CSV Analytics Agent

## Status
Accepted

## Context
The CSV Analytics Agent is an AI analytics system that must process CSV data safely, deterministically, and explainably before feeding results into visualization modules, tools, and agentic LLMs.

## Decision
Adopt a decoupled, multi-stage layered pipeline architecture:
1. **Stage 1 (Data Loader & Validator)**: Validates schema, extension, encoding, and loads CSV safely into a pandas DataFrame.
2. **Stage 2 (Dataset Profiler)**: Computes column statistics, missing value summaries, memory usage, and duplicate counts.
3. **Stage 3 (Insights Engine)**: Evaluates pure business rules on profiles to generate structured evidence and insights.
4. **Stage 4+ (Visualization, Tools, LLM Planner)**: Operates strictly on structured metadata and evidence without rescanning raw CSV DataFrames.

## Consequences
* High performance: No redundant DataFrame re-scanning.
* Testability: Each stage operates on well-defined immutable models.
* Maintainability: Changes to language models or visualization components do not alter ingestion or statistical logic.
