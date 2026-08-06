# ADR-004: Evidence-Based Insights

## Status
Accepted

## Context
The analytics engine must produce explainable and deterministic results that can later be consumed by visualization engines, tool layers, and LLMs. Storing only unstructured text strings obscures underlying facts.

## Decision
Every `Insight` contains a list of structured `Evidence` items describing the `column_name`, `metric_name`, `observed_value`, `threshold`, and `comparison` operator evaluated by business rules.

## Consequences
* Improved explainability: Downstream consumers have programmatic access to underlying metrics.
* Enables precise visualization selection without text parsing.
* Provides deterministic facts for LLM reasoning and agentic tool planning.
