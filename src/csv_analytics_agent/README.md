# 🛠️ Source Architecture & Developer Guide

This directory contains the core implementation of the **CSV Analytics Agent**, structured into clean domain modules following **Domain-Driven Design (DDD)** and SOLID principles.

---

## 📦 Package Organization

```text
src/csv_analytics_agent/
├── config/             # Settings & Environment Configuration
│   ├── __init__.py
│   └── setting.py      # AppSettings & environment loader
├── data/               # Stage 1: Ingestion & Structural Validation
│   ├── __init__.py
│   ├── loader.py       # CSVLoader (encoding auto-detection, pandas loading)
│   └── validator.py    # CSVValidator (file exists, extension, non-empty, schema balance)
├── exceptions/         # Domain Exception Hierarchy
│   ├── __init__.py
│   └── data_errors.py  # CSVAnalyticsError base tree
├── profiler/           # Stage 2: Profiling & Pure Statistics
│   ├── __init__.py
│   ├── models.py       # DatasetProfile, ColumnProfile, Summary Pydantic models
│   ├── profiler.py     # DatasetProfiler orchestrator
│   └── statistics.py   # Pure statistical helper functions
└── insights/           # Stage 3: Business Rules & Evidence Engine
    ├── __init__.py
    ├── generator.py    # InsightGenerator orchestrator
    ├── models.py       # Insight, Evidence, Severity, InsightCategory domain models
    └── rules/          # Domain-specific rule evaluators
        ├── __init__.py
        ├── missing.py      # MissingDataRule evaluator
        ├── duplicates.py   # DuplicateRowsRule evaluator
        └── cardinality.py  # HighCardinalityRule evaluator
```

---

## ⚙️ Module Breakdown

### 1. `config/`
Provides centralized configuration using `pydantic-settings`. Manages environment flags, default encoding candidates (`utf-8`, `latin-1`, `cp1252`, `iso-8859-1`), and threshold constants.

### 2. `data/`
- **`loader.py`**: Loads CSV files safely into `pandas.DataFrame`. Iterates through fallback character encodings if initial UTF-8 decoding fails.
- **`validator.py`**: Performs pre-ingestion validation checks:
  - Verifies file exists on disk.
  - Verifies extension is strictly `.csv`.
  - Verifies file is not zero-byte or empty.
  - Verifies header structural balance.

### 3. `exceptions/`
Houses domain-specific custom exceptions extending `CSVAnalyticsError`:
- `CSVLoaderError`: Base exception for loading issues.
- `CSVEncodingError`: Raised when none of the candidate encodings can decode the file.
- `CSVParsingError`: Raised on malformed rows or structural parsing failure.
- `EmptyCSVError`: Raised on empty or header-only files.

### 4. `profiler/`
- **`profiler.py`**: Orchestrates table profiling. Produces a frozen `DatasetProfile`.
- **`statistics.py`**: Contains pure, side-effect-free functions computing column summary metrics:
  - Numeric columns: mean, standard deviation, min, max, median, 25%/75% quantiles.
  - Categorical columns: distinct count, top categories, frequency distribution.
  - Datetime columns: min date, max date, null count.
- **`models.py`**: Defines frozen Pydantic models: `DatasetProfile`, `DatasetSummary`, `NumericColumnProfile`, `CategoricalColumnProfile`, `DatetimeColumnProfile`.

### 5. `insights/`
- **`generator.py`**: Runs a collection of domain rules over a `DatasetProfile`, collecting and sorting emitted `Insight` objects by severity descending.
- **`models.py`**: Defines `Insight` findings containing `Severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`), `InsightCategory`, and `Evidence` (dictionary of facts).
- **`rules/`**: Individual rule evaluators:
  - `MissingDataRule`: Flags columns exceeding missing value thresholds (e.g. >50% critical, >20% high).
  - `DuplicateRowsRule`: Detects duplicate row ratios.
  - `HighCardinalityRule`: Detects primary key candidates and high-cardinality categorical features.

---

## 💡 How to Add a New Business Rule

Adding new domain analytics rules is simple and requires zero changes to raw data DataFrames:

### Step 1: Implement Rule Evaluator

Create a new file under `src/csv_analytics_agent/insights/rules/my_custom_rule.py`:

```python
from typing import List
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.insights.models import Insight, Evidence, Severity, InsightCategory

class MyCustomRule:
    """Evaluates custom domain conditions on a DatasetProfile."""
    
    def evaluate(self, profile: DatasetProfile) -> List[Insight]:
        insights: List[Insight] = []
        
        # Pure logic operating on frozen profile metadata
        if profile.summary.row_count < 10:
            evidence = Evidence(facts={"row_count": profile.summary.row_count, "min_required": 10})
            insight = Insight(
                title="Small Sample Size Detected",
                category=InsightCategory.DATA_QUALITY,
                description="Dataset contains fewer than 10 records, reducing statistical significance.",
                severity=Severity.LOW,
                evidence=evidence,
            )
            insights.append(insight)
            
        return insights
```

### Step 2: Register Rule in `InsightGenerator`

Add your rule instance to the default rules list in `src/csv_analytics_agent/insights/generator.py`:

```python
from csv_analytics_agent.insights.rules.my_custom_rule import MyCustomRule

def __init__(self, rules=None):
    if rules is None:
        self.rules = [
            MissingDataRule(),
            DuplicateRowsRule(),
            HighCardinalityRule(),
            MyCustomRule(),  # Registered new rule
        ]
```

### Step 3: Add Unit Test

Add a unit test in `tests/insights/rules/test_my_custom_rule.py` ensuring 100% test coverage.

---

## 🧪 Testing Guidelines

Maintain **100% test coverage** for all changes:

```bash
# Run pytest with coverage report
.venv/bin/pytest --cov=src/csv_analytics_agent --cov-report=term-missing
```
