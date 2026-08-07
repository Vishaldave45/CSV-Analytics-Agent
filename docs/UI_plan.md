# Implementation Plan: Streamlit Web Application (Stage 7.5 MVP UI)

Implement a production-grade Streamlit Web Application UI (`streamlit_app/`) for the CSV Analytics Agent, matching the high-tech **LOGIC_OS_2.0** dark UI mockups found in [stitch_csv_insight_agent](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/stitch_csv_insight_agent).

## User Review Required

> [!IMPORTANT]
> **Thin Frontend Architecture**: Streamlit UI components will only render session state and call clean service abstractions (`services/backend.py` and `services/session.py`). All business logic, profiling, insights, rendering, execution, and graph orchestration will stay 100% inside `src/csv_analytics_agent/`.

> [!TIP]
> **LOGIC_OS_2.0 Design Theme**: Modern dark mode palette (`#090d16` background, `#0f172a` container surfaces, `#00f0ff` neon cyan highlights, `#14b8a6` teal accents, custom CSS cards, glowing status pills).

---

## Proposed Component & Page Architecture

### 1. Services Layer (`streamlit_app/services/`)
- **[NEW] `session.py`**: Wraps `st.session_state` keys (`thread_id`, `raw_df`, `profile`, `insights`, `charts`, `messages`, `last_result`, `active_filters`) with safe initializers.
- **[NEW] `backend.py`**: Interoperability bridge connecting Streamlit to Stage 1 Loader, Stage 2 Profiler, Stage 3 Insights, Stage 4 Visualization, and Stage 7.9 `AgentRuntime`.

### 2. UI Components Layer (`streamlit_app/components/`)
- **[NEW] `sidebar.py`**: LOGIC_OS_2.0 branded sidebar displaying active dataset details, proactive insights status, and navigation shortcuts.
- **[NEW] `uploader.py`**: Drag & drop CSV dropzone with sample dataset buttons (*Sales Data*, *Customer Churn*, *Survey Responses*).
- **[NEW] `profile_card.py`**: Summary cards for row count, column count, missing value ratio, memory footprint, and data types.
- **[NEW] `insight_card.py`**: Data quality cards (anomalies, missing data, duplicates, cardinality warnings, and recommendations).
- **[NEW] `chart_view.py`**: Visual chart rendering view displaying Matplotlib/Plotly chart specifications with alternative options.
- **[NEW] `chat_box.py`**: Interactive query chat interface with execution timeline trace (`Router` -> `Retrieval` -> `Planner` -> `Tool` -> `Explainer`), expandable raw data payloads, and suggested follow-up chips.
- **[NEW] `metrics.py`**: KPI metric parameter cards.

### 3. Application Pages (`streamlit_app/pages/` & `app.py`)
- **[NEW] `app.py`**: Main app entrypoint, page configuration (`layout="wide"`, initial theme injection), logo header, and router redirect.
- **[NEW] `assets/styles.css`**: CSS stylesheet implementing LOGIC_OS_2.0 dark mode, cyan accents, glassmorphic cards, and custom scrollbars.
- **[NEW] `pages/1_Upload.py`**: CSV upload & sample dataset loader.
- **[NEW] `pages/2_Dataset.py`**: Dataset overview, data preview table, missing values matrix, and statistical profile.
- **[NEW] `pages/3_Insights.py`**: Quality findings, severe warnings, and empirical evidence lists.
- **[NEW] `pages/4_Visualizations.py`**: Recommended charts, alternative chart picker, and chart renderer.
- **[NEW] `pages/5_AI_Chat.py`**: Conversational agent interface with `AgentRuntime`, execution timeline, and suggested questions.
- **[NEW] `pages/6_History.py`**: Checkpointed conversation history and past tool execution logs.
- **[NEW] `pages/7_Settings.py`**: Runtime configuration (model selection, temperature, max iterations, LangSmith toggle, reset memory).

---

## Verification Plan

### Automated Tests
- Create `tests/test_streamlit_services.py` testing `services/session.py` state initialization and `services/backend.py` pipeline bridge functions.
- Run complete test suite (`.venv/bin/pytest -m "not llm"`) to guarantee zero regression across all 210 existing unit tests.
- Run Ruff linter (`.venv/bin/ruff check .`) and MyPy type checker (`.venv/bin/mypy src streamlit_app`).

### Manual Verification
- Launch Streamlit application locally: `.venv/bin/streamlit run streamlit_app/app.py`.
- Test CSV upload, dataset profiling, insight card rendering, recommended visualization displays, and AI Chat query loops with checkpoint state persistence.
