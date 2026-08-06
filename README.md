# CSV Analytics Agent 📊

A production-grade, evidence-driven CSV Analytics Agent built with Python 3.10+, Pydantic v2, and a deterministic layered pipeline architecture.

---

## 🌟 Project Overview

The **CSV Analytics Agent** converts raw tabular data (CSVs) into deterministic, structured insights backed by empirical evidence. Designed following Domain-Driven Design (DDD) principles, the agent processes datasets through a strict, multi-stage pipeline where statistics and business rules are calculated deterministically before being passed to downstream visualization tools and agentic LLMs.

---

## ✨ Features

- **Stage 1 — Data Loader & Validator**:
  - Validates file paths, extensions (`.csv`), non-empty file sizes, and structural balance.
  - Automatically detects character encodings (`utf-8`, `latin-1`, `cp1252`, `iso-8859-1`).
  - Implements custom exception hierarchies (`CSVLoaderError`, `CSVEncodingError`, `CSVParsingError`, `EmptyCSVError`).
- **Stage 2 — Dataset Profiler**:
  - Computes complete dataset summaries (row counts, column counts, total memory usage).
  - Calculates missing value percentages, duplicate row metrics, and memory distribution.
  - Generates type-specific statistical profiles for numeric, categorical, and datetime columns (mean, std, min, median, max, quantiles, distinct category counts, min/max dates).
  - All outputs serialized as frozen, immutable Pydantic models (`DatasetProfile`).
- **Stage 3 — Insights Engine & Structured Evidence**:
  - Evaluates pure, deterministic business rules on dataset profiles (zero Pandas DataFrame re-scanning).
  - Detects high/medium missing values, duplicate rows, primary key identifier columns, and high cardinality categorical features.
  - Generates structured, explainable findings (`Insight`) backed by empirical facts (`Evidence`).
  - Automatically sorts findings descending by severity priority (`CRITICAL` → `HIGH` → `MEDIUM` → `LOW` → `INFO`).

---

## 🏗️ Project Architecture

```text
                                CSV File
                                   │
                                   ▼
                              CSV Loader
                                   │
                                   ▼
                            Dataset Profiler
                                   │
                                   ▼
                             DatasetProfile
                                   │
                                   ▼
                            Insights Engine
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
            Rule Evaluation                Evidence Creation
                   │                               │
                   └───────────────┬───────────────┘
                                   ▼
                                Insight
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
 Visualization Engine         Analytics Tools             Agentic LLM
```

Everything above the dataset profiler operates strictly on structured, immutable models (`DatasetProfile`, `Insight`, `Evidence`), preventing redundant DataFrame scans and guaranteeing 100% explainability.

---

## 📁 Project Structure

```text
csv-analytics-agent/
├── src/csv_analytics_agent/
│   ├── config/             # Environment settings & configuration
│   ├── data/               # Stage 1: Data loader & CSV validator
│   ├── exceptions/         # Domain-specific exception hierarchy
│   ├── profiler/           # Stage 2: Dataset profiler & pure statistics
│   └── insights/           # Stage 3: Deterministic rules, generator & evidence
│       ├── models.py       # Domain models (Severity, InsightCategory, Evidence, Insight)
│       ├── generator.py    # InsightGenerator orchestrator
│       └── rules/          # Domain-specific business rule evaluators
│           ├── missing.py
│           ├── duplicates.py
│           └── cardinality.py
├── tests/                  # Unit test suite matching src/ structure
├── docs/adr/               # Architectural Decision Records (ADR 001–005)
├── pyproject.toml          # Project configuration & dependencies
└── README.md
```

---

## ⚙️ Requirements

- **Python**: `3.10+`
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

---

## 🚀 Installation

Clone the repository and install all dependencies in editable mode:

```bash
git clone https://github.com/Vishaldave45/CSV-Analytics-Agent.git
cd CSV-Analytics-Agent

# Install dependencies using uv
uv sync

# Or using standard pip
pip install -e ".[dev]"
```

---

## 🧪 Running Tests

Execute the complete Pytest suite:

```bash
uv run pytest
```

---

## 🔍 Linting

Check code formatting and static code quality using Ruff:

```bash
uv run ruff check src/ tests/
```

---

## 🏷️ Type Checking

Verify static type annotations using MyPy:

```bash
uv run mypy src/
```

---

## 📈 Code Coverage

Run unit tests with full line-by-line coverage reports:

```bash
uv run pytest --cov=csv_analytics_agent --cov-report=term-missing
```

Current Test Metrics: **68 passed unit tests**, **100% total coverage**.

---

## 🗺️ Roadmap

### Completed Stages
- [x] **Stage 1 — Data Loader & Validator** (`v0.1.0`)
- [x] **Stage 2 — Dataset Profiler & Pure Statistics** (`v0.2.0`)
- [x] **Stage 3 — Deterministic Insights Engine & Structured Evidence** (`v0.3.0`)

### Planned Stages
- [ ] **Stage 4 — Visualization Recommendation Engine** (Deterministic chart mapping)
- [ ] **Stage 5 — Data Preprocessing Pipeline** (Date/Currency/Boolean normalization)
- [ ] **Stage 6 — Schema Vector Indexing** (FAISS semantic column search)
- [ ] **Stage 7 — Analytics Tool Layer** (LangChain/Custom Tool wrappers)
- [ ] **Stage 8 — Gemini Tool Calling & Agentic Planner**
- [ ] **Stage 9 — LangGraph Stateful Workflows**
- [ ] **Stage 10 — Interactive UI & Session Memory**

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Ensure all new logic is backed by 100% unit test coverage.
2. Run `uv run ruff check .` and `uv run mypy src/` before submitting pull requests.
3. Keep code strictly typed, immutable, and co-located in domain modules.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).