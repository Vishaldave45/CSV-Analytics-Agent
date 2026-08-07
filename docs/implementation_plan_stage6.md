# Implementation Plan: Stage 6 — Deterministic Rule-Based Planner Engine

Stage 6 implements a **Deterministic Rule-Based Planner Engine** (`src/csv_analytics_agent/planner/`) that translates natural-language analytical questions into structured `ExecutionRequest` objects understood by the Stage 5 **Execution Engine Framework**.

The planner is purely deterministic, stateless, and execution-decoupled. It performs **no DataFrame operations, no provider calls, and no statistical computations**. It serves as the baseline planning contract that future LLM Planners (Gemini, OpenAI, Claude) must satisfy in Stage 7+.

Stages 1–5 (**Loader**, **Profiler**, **Insights**, **Visualization**, **Execution Framework**) remain 100% frozen and preserved.

---

## Target Architecture

```text
               User Question + Column Schema
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Stage 6: Deterministic Rule-Based Planner Engine       │
 │                                                         │
 │  1. Query Parser    ──> Extract Intent & Parameters     │
 │  2. Rule Engine     ──> Match Synonyms & Rules          │
 │  3. Capability Matcher ──> Validate via Registry        │
 └───────────────────────────┬─────────────────────────────┘
                             │
                             ▼
                     ExecutionRequest
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │ Stage 5: Capability Engine Framework                 │
  │ (CapabilityRegistry ──> Domain Engine ──> Provider)  │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
                      ExecutionResult
```

---

## Observability & Reasoning Trace Feature

Every `PlannerResult` payload includes full execution trace metadata:

```python
PlannerResult(
    execution_request=ExecutionRequest(...),
    confidence=0.95,
    matched_rule="average|mean -> aggregate(operation='mean')",
    reasoning_trace=[
        "Extracted raw query: 'What is the average salary?'",
        "Matched intent 'AGGREGATE' via synonym 'average'",
        "Resolved target column 'salary' from dataset schema",
        "Discovered capability 'aggregate' in CapabilityRegistry",
        "Generated ExecutionRequest for capability 'aggregate'",
    ],
    success=True,
    error_message=None,
)
```

---

## Target Folder Structure

```text
src/
└── csv_analytics_agent/
    └── planner/
        ├── __init__.py
        ├── models.py       # Phase 1: IntentType, Parameter, ParsedIntent, PlannerResult, PlannerMetadata
        ├── rules.py        # Phase 2: Synonym mappings & rule definitions
        ├── parser.py       # Phase 3: QueryParser for column & parameter extraction
        ├── matcher.py      # Phase 4: CapabilityMatcher querying CapabilityRegistry
        └── planner.py      # Phase 5: RulePlanner orchestrator

tests/
└── planner/
    ├── __init__.py
    ├── test_models.py      # Phase 1 Tests
    ├── test_rules.py       # Phase 2 Tests
    ├── test_parser.py      # Phase 3 Tests
    ├── test_matcher.py     # Phase 4 Tests
    ├── test_planner.py     # Phase 5 Tests
    └── test_integration.py # Phase 6 Tests
```

---

## Proposed Phase-by-Phase Execution Plan

### Phase 1 — Planner Domain Models (`planner/models.py`)
* **Goal**: Define immutable Pydantic v2 domain models for planning intent, parameters, and traces.
* **Deliverables**:
  * `IntentType(str, Enum)`: `AGGREGATE`, `FILTER`, `GROUP`, `SORT`, `TOP_N`, `UNKNOWN`
  * `Parameter(BaseModel, frozen=True)`: `name: str`, `value: Any`, `raw_text: str`
  * `ParsedIntent(BaseModel, frozen=True)`: `intent_type: IntentType`, `target_columns: list[str]`, `parameters: dict[str, Any]`, `raw_query: str`
  * `PlannerResult(BaseModel, frozen=True)`: `execution_request: ExecutionRequest | None`, `confidence: float`, `matched_rule: str | None`, `reasoning_trace: list[str]`, `success: bool`, `error_message: str | None`
  * `PlannerMetadata(BaseModel, frozen=True)`: `name: str`, `version: str`, `description: str`

---

### Phase 2 — Rule Engine & Synonym System (`planner/rules.py`)
* **Goal**: Implement configurable rule system mapping keywords/synonyms to analytical intent.
* **Deliverables**:
  * Synonyms mapping:
    * `mean`, `average`, `avg` $\rightarrow$ `aggregate(operation='mean')`
    * `max`, `maximum`, `highest`, `peak` $\rightarrow$ `aggregate(operation='max')`
    * `min`, `minimum`, `lowest` $\rightarrow$ `aggregate(operation='min')`
    * `total`, `sum` $\rightarrow$ `aggregate(operation='sum')`
    * `count`, `number of` $\rightarrow$ `aggregate(operation='count')`
    * `top`, `first`, `best` $\rightarrow$ `top_n(order='desc')`
    * `bottom`, `worst`, `lowest n` $\rightarrow$ `top_n(order='asc')`
    * `group by`, `grouped by`, `per`, `by` $\rightarrow$ `group`
    * `sort`, `order by`, `ascending`, `descending` $\rightarrow$ `sort`
    * `greater than`, `less than`, `equal to`, `above`, `below` $\rightarrow$ `filter`

---

### Phase 3 — Query Parser (`planner/parser.py`)
* **Goal**: Implement `QueryParser` to extract operations, column names (matched against dataset schema), numbers, and comparison operators.
* **Deliverables**:
  * `parse(query: str, available_columns: list[str]) -> ParsedIntent`
  * Column matching (case-insensitive substring/word match against DataFrame columns).
  * Numeric parameter extraction (e.g. "top 10" $\rightarrow$ `n=10`, "older than 30" $\rightarrow$ `value=30`).

---

### Phase 4 — Capability Matcher (`planner/matcher.py`)
* **Goal**: Implement `CapabilityMatcher` that validates `ParsedIntent` against `CapabilityRegistry`.
* **Deliverables**:
  * `match(intent: ParsedIntent, registry: CapabilityRegistry) -> tuple[CapabilityDescriptor, dict[str, Any]]`
  * Validates capability presence in registry without performing execution.

---

### Phase 5 — Deterministic Rule Planner Orchestrator (`planner/planner.py`)
* **Goal**: Implement `RulePlanner` orchestrating `QueryParser`, Rule Engine, and `CapabilityMatcher`.
* **Deliverables**:
  * `plan(query: str, available_columns: list[str], registry: CapabilityRegistry) -> PlannerResult`
  * Generates confidence scores, matched rule summaries, and step-by-step reasoning traces.

---

### Phase 6 — Integration & End-to-End Pipeline
* **Goal**: Connect Stage 6 Planner to Stage 5 Execution Framework.
* **Deliverables**:
  * Demonstrate: Question $\rightarrow$ `RulePlanner` $\rightarrow$ `ExecutionRequest` $\rightarrow$ `CapabilityRegistry` $\rightarrow$ `AnalyticsEngine` $\rightarrow$ `PandasProvider` $\rightarrow$ `ExecutionResult`.

---

### Phase 7 — Comprehensive Test Suite & Quality Checks (`tests/planner/`)
* **Goal**: Validate unit test coverage and static checks across all planner modules.
* **Deliverables**:
  * Unit tests for models, rules, parser, matcher, planner orchestrator, and integration flows.
  * Static type checking (`mypy`), linting (`ruff`), and test suite (`pytest`) pass rate 100%.

---

## Verification Plan

1. **Static Analysis**: `uv run mypy src`
2. **Linter & Formatting**: `uv run ruff check .` and `uv run ruff format --check .`
3. **Automated Test Suite**: `uv run pytest`
