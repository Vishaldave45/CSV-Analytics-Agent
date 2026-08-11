# LOGIC_OS 2.0 — CSV Analytics Agent
### Setup, Configuration & Run Guide

This guide gets the project running from a clean checkout: environment setup,
API keys, running the Streamlit app, running the test suite, and a map of
every part of the codebase.

---

## 1. What this project is

A production-style **CSV analytics agent**: upload a CSV, get an automatic
statistical profile, proactive data-quality insights, auto-recommended
charts, and a LangGraph-powered chat agent (backed by Google Gemini) that
can answer natural-language questions about the data — with a semantic
memory layer (FAISS + sentence-transformers) so it recalls prior context.

- **Backend / core library**: `src/csv_analytics_agent/` — pure Python,
  framework-agnostic (profiling, insights, execution engine, LangGraph
  agent, persistence).
- **Frontend**: `streamlit_app/` — a multi-page Streamlit UI.
- **Tests**: `tests/` — 200+ unit/integration tests (pytest).

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 – 3.12 | The project targets `>=3.10` (see `pyproject.toml`). |
| pip | latest | `python -m pip install --upgrade pip` |
| ~3–4 GB free disk | — | `sentence-transformers` pulls in PyTorch, which is large. |
| Google AI Studio API key | free tier | Needed only for the AI Chat page (Gemini). Everything else (upload, profiling, insights, charts) works without it. |

> **Tip:** if you only want to explore upload/profiling/insights/charts and
> don't need the AI chat, you can skip the API key and skip installing
> `sentence-transformers` / `faiss-cpu` entirely (see §4.2 "Lite install").

---

## 3. Project structure at a glance

```
csv-analytics-agent/
├── src/csv_analytics_agent/     # Core library (framework-agnostic)
│   ├── data/                    # CSV loading & validation
│   ├── preprocessing/           # Type coercion
│   ├── profiler/                # Statistical profiling engine
│   ├── insights/                # Rule-based data-quality insight generator
│   ├── visualization/           # Chart recommendation + rendering (matplotlib)
│   ├── execution/                # Sandboxed pandas execution engine
│   ├── graph/                    # LangGraph agent (planner, router, tools, memory)
│   ├── llm/                       # Gemini LLM wrapper + rate limiting
│   ├── memory/                    # FAISS semantic memory store
│   ├── persistence/               # SQLAlchemy models + repository (dataset cache)
│   ├── observability/             # LangSmith tracing hooks
│   └── config/                    # Pydantic Settings (.env-driven)
├── streamlit_app/                 # Streamlit UI
│   ├── app.py                     # Entry point
│   ├── pages/                     # 1_Upload … 7_Settings
│   ├── components/                # Reusable UI building blocks
│   ├── services/                  # Session state + backend orchestration
│   ├── assets/styles.css          # Design system (dark glassmorphic)
│   └── sample_data/                # 3 sample CSVs to try immediately
├── tests/                          # Mirrors src/ + streamlit_app/ structure
├── alembic/                         # DB migrations (dataset cache table)
├── docs/                            # SRS, ADRs, implementation plan
├── pyproject.toml                   # Dependencies (uv/pip installable)
├── pytest.ini / ruff.toml / mypy.ini
└── .env.example                     # Copy to .env and fill in
```

---

## 4. Installation

### 4.1 Full install (recommended — enables AI chat + semantic memory)

```bash
# 1. Clone / unzip the project, then cd into it
cd csv-analytics-agent

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install the project (editable) + all dependencies
pip install -e .

# If you use uv instead of pip:
#   uv sync
```

This installs everything declared in `pyproject.toml`, including
`langgraph`, `langchain-google-genai`, `faiss-cpu`, and
`sentence-transformers` (which brings in PyTorch — this step can take a
few minutes and ~2–3 GB of disk).

### 4.2 Lite install (no AI chat / no semantic memory)

If you just want Upload → Dataset DNA → Insights → Visualizations:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pydantic pydantic-settings pandas numpy matplotlib \
            streamlit structlog pyrate-limiter "sqlalchemy>=2.0" alembic \
            python-dotenv
```

The **5_AI_Chat** page will show a clear error if `langgraph` /
`langchain-google-genai` / `faiss-cpu` aren't installed — every other page
works normally.

### 4.3 Dev tools (optional, for contributing)

```bash
pip install -e ".[dev]"     # if using the dependency-group syntax, or:
pip install pytest pytest-cov mypy pandas-stubs ruff
```

---

## 5. Configuration (`.env`)

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

```ini
# Application Settings
DEFAULT_ENCODING=utf-8
MAX_CSV_SIZE_MB=500

# LLM API Configuration
# Get your FREE key at: https://aistudio.google.com/app/apikey  (starts with AIzaSy...)
GOOGLE_API_KEY=your_google_ai_studio_key_here

# LangSmith Observability & Tracing (optional — leave disabled if unused)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=csv-analytics-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_SESSION=development
LANGCHAIN_TAGS=local,csv-agent
```

- **`GOOGLE_API_KEY`** — required only for the **AI Chat** page. Get a free
  key at https://aistudio.google.com/app/apikey. Without it, every other
  page (Upload, Dataset DNA, Insights, Visualizations, History, Settings)
  works fully.
- You can also paste the API key directly into the **Settings** page inside
  the running app — it will write it into `.env` for you.
- **LangSmith** tracing is fully optional and off by default
  (`LANGCHAIN_TRACING_V2=false`). Turn it on only if you have a LangSmith
  account and want request/response tracing.

---

## 6. Running the app

```bash
source .venv/bin/activate     # if not already active
streamlit run streamlit_app/app.py
```

Then open the URL Streamlit prints (defaults to `http://localhost:8501`).

**First run walkthrough:**
1. **Upload** page — drag in a CSV, or click one of the 3 bundled sample
   datasets in `streamlit_app/sample_data/` (`sales_data.csv`,
   `customer_churn.csv`, `survey_responses.csv`).
2. **Dataset DNA** — auto-generated statistical profile (types, nulls,
   cardinality, distributions).
3. **Insights** — proactive, rule-based data-quality findings (missing
   data, duplicates, high-cardinality columns, etc.).
4. **Visualizations** — auto-recommended charts based on column types.
5. **AI Chat** — ask questions in plain English (requires `GOOGLE_API_KEY`).
6. **History** — past conversation threads (SQLite-backed).
7. **Settings** — manage your API key and model parameters from the UI.

---

## 7. Running tests

```bash
source .venv/bin/activate
pytest
```

- The suite has **200+ tests** covering the loader, validator, profiler,
  insights, execution engine, LangGraph nodes, persistence, and Streamlit
  service layer.
- One test (`test_gemini_real_api_smoke_test`) makes a **live call** to the
  Gemini API and is excluded by default (`pytest.ini` sets
  `addopts = -m "not llm"`). To run it explicitly, with a real key and
  network access:
  ```bash
  pytest -m llm
  ```
- Coverage report:
  ```bash
  pytest --cov=src/csv_analytics_agent --cov-report=term-missing
  ```
- Lint / type-check:
  ```bash
  ruff check src streamlit_app tests
  mypy src
  ```

---

## 8. Database & migrations

The app uses a small local SQLite database (`app_metadata.db` for dataset
caching) — LangGraph checkpointing is kept in-memory and does not persist to
`sessions.db`.
automatically on first run. If you change the persistence models, generate
a new migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install python-dotenv` (already added to `pyproject.toml` in this build — re-run `pip install -e .`). |
| AI Chat page errors "DataFrame context is required" | This is expected if you open that page directly without uploading a CSV first — go to **Upload** first. |
| `GOOGLE_API_KEY` errors on the Chat page | Add a valid key via the **Settings** page or `.env`; get one free at https://aistudio.google.com/app/apikey. |
| `sentence-transformers` / `faiss-cpu` install is slow or huge | Expected — it installs PyTorch. Use the **Lite install** (§4.2) if you don't need AI chat/semantic memory. |
| Live Gemini test fails in CI/offline environments | Expected — it's excluded by default; only runs with `pytest -m llm` + network + a real key. |
| Port already in use | `streamlit run streamlit_app/app.py --server.port 8502` |

---

## 10. What changed in this pass

A full audit was performed before packaging this build:

- ✅ All 165 Python files compile cleanly (`py_compile`).
- ✅ Every module in `src/csv_analytics_agent` and `streamlit_app` imports
  without error.
- ✅ Full test suite: **204 passed**, 1 intentionally deselected (live API
  smoke test).
- ✅ Fixed a missing dependency: `python-dotenv` was used in code but never
  declared in `pyproject.toml`.
- ✅ Fixed the live-API test so it no longer breaks offline/CI test runs
  (`pytest.ini` now deselects `-m llm` tests by default).
- ✅ Cleaned up lint issues (ambiguous variable names, unused loop
  variables, redundant file-open modes) flagged by `ruff`.
- ✅ **UI/UX refinement**: extended `streamlit_app/assets/styles.css` with a
  full polish layer so every native Streamlit widget (inputs, selects,
  tabs, dataframes, metrics, alerts, file uploader, chat bubbles, sidebar
  nav, tooltips) matches the custom dark glassmorphic design system,
  instead of falling back to default Streamlit styling. Added
  accessible focus states and responsive breakpoints for the bento grid.
  Aligned `.streamlit/config.toml`'s base theme colors with the CSS design
  tokens so native and custom components look cohesive.
  Replaced hardcoded hex colors in `sidebar.py` with the shared CSS
  variables for long-term maintainability.

---

## 11. Support

- Architecture decisions: `docs/adr/`
- Original spec: `docs/SRS_CSV_Analytics_Agent.docx`
- Implementation plan: `docs/implementation_plan.md`
