# Implementation Plan: Stage 5 — Capability & Execution Engine Framework

Evolve Stage 5 from standalone tool scripts into a **Unified Capability & Execution Engine Framework** (`src/csv_analytics_agent/engine/`). This architecture decouples high-level analytical intent (Domain Engines) from underlying library implementations (Providers) cataloged within a central `CapabilityRegistry`.

Stages 1–4 (**Loader**, **Profiler**, **Insights**, **Visualization**) remain 100% frozen and preserved.

---

## Architecture Overview

```text
src/
└── csv_analytics_agent/
    └── engine/
        ├── __init__.py          # Public API exports
        ├── models.py            # ExecutionStatus, CapabilityType, CapabilityDescriptor, ExecutionRequest, ExecutionResult[T]
        ├── base.py              # Abstract BaseEngine and BaseProvider interfaces
        ├── registry.py          # CapabilityRegistry for registration, discovery, and execution
        ├── exceptions.py        # Engine-specific exceptions (EngineError, ExecutionError, RegistryError)
        ├── domain/              # Specialized Business Engines
        │   ├── __init__.py
        │   ├── analytics.py     # AnalyticsEngine (Aggregations, Filtering, Grouping, Sorting)
        │   ├── statistics.py    # StatisticsEngine (Correlation, Distributions, Hypothesis Testing)
        │   └── viz_adapter.py   # VisualizationAdapter (Adapts Stage 4 Recommender & Renderer)
        └── providers/           # Execution Infrastructure Providers
            ├── __init__.py
            ├── pandas_provider.py
            └── scipy_provider.py
```

---

## User Review Required

> [!IMPORTANT]
> **Key Architecture Confirmations:**
> 1. **Package Directory**: The new capability engine framework will live under `src/csv_analytics_agent/engine/` to distinguish it from basic tools.
> 2. **Stage 1–4 Safety**: Existing modules (`data`, `profiler`, `insights`, `visualization`) remain completely unchanged.
> 3. **Incremental Phase Execution**: Work will proceed phase-by-phase with verification (`mypy`, `ruff`, `pytest`) at each step.

---

## Proposed Phase-by-Phase Implementation Plan

### Phase 1 — Domain Models & Core Interfaces
Establish immutable Pydantic v2 domain models and abstract base classes.

#### [NEW] [models.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/models.py)
* Define `ExecutionStatus` (`SUCCESS`, `FAILED`, `CANCELLED`).
* Define `CapabilityType` (`ANALYTICS`, `STATISTICS`, `VISUALIZATION`, `FORECASTING`, `MACHINE_LEARNING`).
* Define `CapabilityDescriptor` (metadata, OpenAPI JSON schema of parameters, capability type).
* Define `ExecutionRequest` (capability name, target columns, parameters dictionary).
* Define `ExecutionResult[T]` (generic result payload with execution status, data payload `T`, execution time in ms).

#### [NEW] [base.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/base.py)
* Define `BaseProvider` abstract base class.
* Define `BaseEngine` abstract base class.

#### [NEW] [exceptions.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/exceptions.py)
* Define `EngineError`, `CapabilityNotFoundError`, `ExecutionError`, `ProviderError`.

---

### Phase 2 — Capability Registry
Build the central discovery authority and execution dispatcher.

#### [NEW] [registry.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/registry.py)
* Implement `CapabilityRegistry` class:
  * `register(descriptor: CapabilityDescriptor, engine: BaseEngine) -> None`
  * `get(name: str) -> CapabilityDescriptor`
  * `export_llm_tool_schemas() -> list[dict[str, Any]]`
  * `execute(request: ExecutionRequest, df: pd.DataFrame) -> ExecutionResult[Any]`

#### [NEW] [test_registry.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/engine/test_registry.py)
* Unit tests for registration, schema generation, lookup, and execution routing.

---

### Phase 3 — Analytics Engine & Pandas Provider
Implement data manipulation capabilities (filtering, aggregation, grouping, sorting).

#### [NEW] [pandas_provider.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/providers/pandas_provider.py)
* Encapsulate pandas DataFrame methods (`groupby`, `mean`, `sum`, `filter`, `sort_values`).

#### [NEW] [analytics.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/domain/analytics.py)
* Implement `AnalyticsEngine` processing `ANALYTICS` capabilities using `PandasProvider`.

#### [NEW] [test_analytics_engine.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/engine/test_analytics_engine.py)
* Unit tests for aggregation, filtering, and sorting capabilities.

---

### Phase 4 — Statistics Engine & SciPy Provider
Implement statistical analysis capabilities (correlation, distribution analysis).

#### [NEW] [scipy_provider.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/providers/scipy_provider.py)
* Encapsulate `scipy.stats` computations (correlation, z-scores, p-values).

#### [NEW] [statistics.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/domain/statistics.py)
* Implement `StatisticsEngine` for `STATISTICS` capabilities.

---

### Phase 5 — Visualization Adapter Engine
Adapt Stage 4 recommender & renderer into the Capability Registry.

#### [NEW] [viz_adapter.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/engine/domain/viz_adapter.py)
* Adapt Stage 4 `recommend_visualizations` and `render_chart` into a unified capability.

---

### Phase 6 — Full Verification & Integration Suite
Validate type safety, linting, and 100% test pass rate across the workspace.

---

## Verification Plan

### Automated Tests
* Static Type Checking: `./.venv/bin/mypy src`
* Code Style & Formatting: `./.venv/bin/ruff check src tests`
* Unit Test Suite: `./.venv/bin/pytest`

### Acceptance Criteria
* Zero errors in MyPy and Ruff.
* All existing tests (Stages 1–4) continue to pass without modification.
* 100% test coverage on new engine models, registry, and engines.
