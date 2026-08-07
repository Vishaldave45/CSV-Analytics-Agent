<div align="center">

# 📊 CSV Analytics Agent

**A production-grade, evidence-driven tabular analytics framework built with Python 3.10+, Pydantic v2, and a deterministic layered pipeline & execution engine architecture.**

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Release](https://img.shields.io/badge/release-v0.6.0-blue?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Vishaldave45/CSV-Analytics-Agent/releases/tag/v0.6.0)
[![Tests](https://img.shields.io/badge/tests-147%20passed-2ea44f?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Vishaldave45/CSV-Analytics-Agent)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-261230?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue?style=for-the-badge&logo=python&logoColor=white)](https://github.com/python/mypy)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 🌟 Overview

The **CSV Analytics Agent** converts raw tabular data (`.csv` files) into structured, evidence-backed insights, renderer-independent visualizations, executable analytical capabilities, and deterministic natural-language query plans. Designed around **Domain-Driven Design (DDD)** principles, the agent processes datasets through a strict, multi-stage pipeline where statistics, business rules, visualization recommendations, capability execution engines, and query planning operate deterministically before being exposed to agentic LLM planners or LangGraph workflows.

> [!IMPORTANT]
> **Deterministic First, LLM Second**: Statistics, insights, visualization rules, capability execution, and query planning are evaluated deterministically using immutable Pydantic v2 models and provider abstractions. This eliminates hallucinated data summaries and guarantees 100% explainability and safety.

---

## ✨ Key Capabilities

| Feature | Description |
| :--- | :--- |
| 🛡️ **Robust Data Loader** | Validates structural integrity, missing files, non-empty bounds, and automatically detects encodings (`utf-8`, `latin-1`, `cp1252`, `iso-8859-1`). |
| 📊 **Pure Dataset Profiler** | Computes missing value ratios, row duplicates, memory distribution, and column-level statistical profiles without side effects. |
| 🔍 **Evidence Engine** | Pure business rules evaluate immutable dataset profiles to generate structured findings (`Insight`) backed by empirical facts (`Evidence`). |
| 🎨 **Visualization Recommendation** | Pure rule engine maps dataset statistical profiles to optimal, renderer-independent chart specifications (`HISTOGRAM`, `BAR`, `LINE`, `SCATTER`, `BOXPLOT`, `PIE`, `HEATMAP`) and Matplotlib rendering. |
| ⚡ **Execution Engine Framework** | Decouples high-level domain capabilities (`AnalyticsEngine`, `VisualizationEngine`) from underlying libraries (`PandasProvider`) registered inside a central `CapabilityRegistry`. |
| 🧩 **Deterministic Rule Planner** | Translates natural-language questions into `ExecutionRequest` payloads with confidence scores and reasoning trace logs (`RulePlanner`, `QueryParser`, `CapabilityMatcher`). |
| 🤖 **LLM Tool Schema Export** | `CapabilityRegistry` automatically exports function-calling JSON schemas for OpenAI, Anthropic, and Gemini LLM function-calling planners. |
| 🧪 **Comprehensive Test Suite** | Every module, validation guard, statistical evaluator, provider, engine, planner rule, and exception path is tested with full statement coverage. |

---

## 🏗️ Architecture & Pipeline Flow

The framework follows a decoupled 6-tier architecture:

```mermaid
flowchart TD
    UserQuery["💬 User Question"] -->|Stage 6: Rule Planner| Planner(RulePlanner & QueryParser)
    Planner -->|Capability Discovery| Reg(CapabilityRegistry)
    Planner -->|Emit Payload| ExecReq["📦 ExecutionRequest (Confidence & Trace)"]
    
    RawCSV[📄 Raw CSV File] -->|Stage 1: Load & Validate| Loader(CSVLoader & CSVValidator)
    Loader -->|Clean DataFrame| Profiler(DatasetProfiler)
    Profiler -->|Immutable Metadata| Profile["❄️ DatasetProfile"]
    Profile -->|Stage 3: Evidence Engine| Insights["💡 List[Insight]"]
    Profile & Insights -->|Stage 4: Visualization| Viz(recommend_visualizations & render_chart)
    
    ExecReq & Reg -->|Stage 5: Execution Engine| Engine(AnalyticsEngine / VisualizationEngine)
    Engine -->|Dynamic Provider Dispatch| Provider(PandasProvider)
    Provider -->|Execute Operation| Result["📦 ExecutionResult[T]"]
```

### Layer Responsibilities

```text
                           ┌────────────────────────┐
                           │      Raw CSV File      │
                           └───────────┬────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 1 — Data Ingestion & Validation Layer                               │
 │ (Handles encoding auto-detection, schema checks, structural balance)     │
 └─────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 2 — Dataset Profiling & Statistical Engine                          │
 │ (Row/Col summary, Missing values, Memory distribution, Column profiles)  │
 └─────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 3 — Insights Engine & Structured Evidence Generation                │
 │ (Evaluates missing, duplicates, cardinality; emits Insight & Evidence)    │
 └─────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 4 — Visualization Recommendation & Rendering Engine                 │
 │ (Maps statistical metadata to ChartSpecification & renders Matplotlib PNG)│
 └─────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 5 — Execution Engine Framework (`execution/`)                       │
 │ (CapabilityRegistry ──> Domain Engines ──> Providers ──> Libraries)       │
 └─────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Stage 6 — Deterministic Rule-Based Planner Engine (`planner/`)            │
 │ (User Question ──> RulePlanner ──> ExecutionRequest ──> ExecutionResult)   │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

### Installation

Clone the repository and set up your virtual environment using `uv` (recommended) or `pip`:

```bash
# Clone the repository
git clone https://github.com/Vishaldave45/CSV-Analytics-Agent.git
cd CSV-Analytics-Agent

# Sync dependencies with uv (creates .venv automatically)
uv sync

# Or using standard pip in editable mode
pip install -e ".[dev]"
```

### Python API Example

```python
from pathlib import Path
from csv_analytics_agent.data import CSVLoader
from csv_analytics_agent.profiler import DatasetProfiler
from csv_analytics_agent.execution import (
    CapabilityRegistry,
    AnalyticsEngine,
    VisualizationEngine,
)
from csv_analytics_agent.planner import RulePlanner

# 1. Load CSV & Profile
df = CSVLoader(Path("data/sample_dataset.csv")).load()
profile = DatasetProfiler().profile(df)

# 2. Setup Execution Framework & Registry
registry = CapabilityRegistry()
analytics_engine = AnalyticsEngine()
viz_engine = VisualizationEngine()

for desc in analytics_engine.list_capabilities():
    registry.register(desc, analytics_engine)
for desc in viz_engine.list_capabilities():
    registry.register(desc, viz_engine)

# 3. Translate Question using Stage 6 Deterministic Planner
planner = RulePlanner()
question = "What is the average salary?"
columns = list(df.columns)

plan_result = planner.plan(question, columns, registry)

print(f"Confidence: {plan_result.confidence}")
print(f"Matched Rule: {plan_result.matched_rule}")
print("Reasoning Trace:")
for step in plan_result.reasoning_trace:
    print(f"  - {step}")

# 4. Execute the planned request deterministically
if plan_result.success and plan_result.execution_request:
    req = plan_result.execution_request
    engine = registry.get_engine(req.capability_name)
    exec_result = engine.execute_capability(req, df)
    print(f"\nExecution Outcome ({exec_result.status.value}): {exec_result.data}")
```

---

## 🧩 Domain Models & Exceptions

### Domain Models (`planner/models.py`, `execution/models.py`, `visualization/models.py`, `insights/models.py`)

| Model | Immutability | Description |
| :--- | :---: | :--- |
| `PlannerResult` | `frozen=True` | Planning output container holding `ExecutionRequest`, `confidence`, `matched_rule`, and `reasoning_trace`. |
| `ParsedIntent` | `frozen=True` | Extracted analytical intent, target columns, parameters, and raw query string. |
| `IntentRule` | `frozen=True` | Declarative synonym rule mapping keywords to analytical intents. |
| `CapabilityDescriptor` | `frozen=True` | Metadata defining a capability name, description, JSON schema, and default provider. |
| `ExecutionRequest` | `frozen=True` | Payload requesting capability execution with column targets and parameters. |
| `ExecutionResult[T]` | `frozen=True` | Type-safe generic result wrapper with status, message, payload data `T`, and timing. |
| `DatasetProfile` | `frozen=True` | Complete statistical breakdown of tabular dataset. |
| `ChartSpecification` | `frozen=True` | Renderer-independent chart definition (type, title, axes, description). |

---

## 🛠️ Project Structure

```text
csv-analytics-agent/
├── src/csv_analytics_agent/
│   ├── config/             # Environment settings & configuration management
│   ├── data/               # Stage 1: Data loader, encoding detector & CSV validator
│   ├── profiler/           # Stage 2: Dataset profiler & pure column statistics
│   ├── insights/           # Stage 3: Deterministic rules, generator & evidence
│   ├── visualization/      # Stage 4: Chart recommendations & Matplotlib renderer
│   ├── execution/          # Stage 5: Execution Engine Framework
│   │   ├── models.py       # Execution domain models
│   │   ├── base.py         # Abstract base classes (BaseProvider, BaseEngine)
│   │   ├── exceptions.py   # Execution exception hierarchy
│   │   ├── registry.py     # CapabilityRegistry & LLM tool schema exporter
│   │   ├── providers/      # PandasProvider encapsulating pandas operations
│   │   └── domain/         # AnalyticsEngine & VisualizationEngine adapters
│   ├── planner/            # Stage 6: Deterministic Rule-Based Planner Engine
│   │   ├── models.py       # Planner domain models (PlannerResult, ParsedIntent)
│   │   ├── rules.py        # Synonym rule definitions & RuleEngine
│   │   ├── parser.py       # QueryParser extracting columns & numeric parameters
│   │   ├── matcher.py      # CapabilityMatcher discovering CapabilityRegistry
│   │   └── planner.py      # RulePlanner orchestrator
│   └── exceptions/         # Base exceptions
├── tests/                  # Complete unit test suite (147 tests)
│   ├── config/
│   ├── data/
│   ├── exceptions/
│   ├── execution/
│   ├── insights/
│   ├── planner/
│   ├── profiler/
│   └── visualization/
├── pyproject.toml          # Project metadata, dependencies & tool settings
├── mypy.ini                # Strict MyPy configuration
├── ruff.toml              # Ruff linter & formatter rules
└── README.md               # Root documentation
```

---

## 🧪 Quality Assurance & Testing

The project maintains strict quality controls:

```bash
# Code linting & style enforcement with Ruff
uv run ruff check .

# Code formatting check
uv run ruff format --check .

# Strict static type checking with MyPy
uv run mypy src

# Run pytest suite
uv run pytest
```

### Current Verification Metrics

- **Unit Tests**: `147 passed` in `0.93s`
- **Type Safety**: `0 errors` (Strict MyPy mode across 45 source files)
- **Formatting**: 100% compliant with Ruff standards

---

## 🗺️ Product Roadmap

- [x] **Stage 1 — Data Loader & Validator** (`v0.1.0`)
  - Auto-encoding detection, file checks, structural validation.
- [x] **Stage 2 — Dataset Profiler & Pure Statistics** (`v0.2.0`)
  - Summary metrics, missing/duplicate analytics, column-level profiles.
- [x] **Stage 3 — Deterministic Insights Engine & Evidence** (`v0.3.0`)
  - Pure rule evaluation (`MissingDataRule`, `DuplicateRowsRule`, `HighCardinalityRule`), severity ranking.
- [x] **Stage 4 — Visualization Recommendation & Rendering Engine** (`v0.4.0`)
  - Automatic chart mapping and Matplotlib rendering engine.
- [x] **Stage 5 — Execution Engine Framework** (`v0.5.0`)
  - Decoupled `CapabilityRegistry`, `AnalyticsEngine`, `VisualizationEngine`, `PandasProvider`.
- [x] **Stage 6 — Deterministic Rule-Based Planner Engine** (`v0.6.0`)
  - `RulePlanner`, `QueryParser`, `CapabilityMatcher`, confidence scoring, and reasoning trace logs.
- [ ] **Stage 7 — LangChain / LlamaIndex Tool Integrations** (`v0.7.0`)
  - Reusable agent tool adapters for LLM frameworks.
- [ ] **Stage 8 — Gemini Tool Calling & Agentic Planner** (`v0.8.0`)
  - Intent recognition and multi-step query decomposition.
- [ ] **Stage 9 — LangGraph Stateful Workflows** (`v0.9.0`)
  - Cyclic stateful workflows and multi-agent collaboration.
- [ ] **Stage 10 — Interactive UI & Session Memory** (`v1.0.0`)
  - Web dashboard with persistent session history.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Ensure all new logic is backed by comprehensive unit tests.
2. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, and `uv run pytest` before submitting pull requests.
3. Keep code strictly typed, immutable, and co-located in domain modules.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).