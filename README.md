# 🤖 CSV Analytics Agent

> An agentic tabular data analytics engine that allows users to upload CSV datasets, ask questions in natural language, and receive data-driven explanations, interactive visualizations, DataFrames, and downloadable analytical results.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://ai.google.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Runtime-261230?style=for-the-badge)](https://www.langchain.com/langgraph)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Memory-0467DF?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![Tests](https://img.shields.io/badge/Tests-475%20passed-2ea44f?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Vishaldave45/CSV-Analytics-Agent)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📸 Demo

The **CSV Analytics Agent** provides an interactive workspace for exploring uploaded datasets through natural language queries.

<p align="center">
  <img src="docs/images/demo.png" alt="CSV Analytics Agent AI Workspace" width="100%">
</p>

### Feature Screens

| Feature Screen | Image Asset Link | Description |
| :--- | :--- | :--- |
| **Dataset Upload & Profiling** | `![Upload Screen](docs/images/dataset-overview.png)` | Upload CSV datasets with auto-encoding detection, coercing numeric/date fields, and rendering dataset DNA profiles. |
| **Natural Language Reasoning** | `![AI Chat Narrative](docs/images/analysis-result.png)` | Explains complex analytical questions in Markdown while separating textual answers from data artifacts. |
| **Interactive Visual Analytics** | `![Plotly Chart](docs/images/visualization.png)` | Generates interactive Plotly and Matplotlib charts (Histograms, Bar Charts, Scatter Plots, Heatmaps). |
| **DataFrame & CSV Export** | `![Data Table](docs/images/dataframe-result.png)` | Displays bounded DataFrame tables with interactive sorting and CSV export options. |

---

## 📌 Overview

The **CSV Analytics Agent** is an end-to-end tabular data intelligence platform built upon **Clean Architecture** and **Domain-Driven Design (DDD)** principles.

The platform combines **LangGraph-based workflow orchestration**, **LangChain Core** and **Gemini** for LLM interaction, **Sentence Transformers** and **FAISS** for semantic column retrieval, and **Python/Pandas** for deterministic tabular analysis. Analytical results are transformed into textual explanations and structured artifacts such as charts and tables before being rendered through Streamlit.

> [!IMPORTANT]
> **Deterministic First, LLM Second**: All statistical calculations, dataset profiling, rule evaluations, and chart specifications are calculated **deterministically** using pure Python, Pandas, and immutable Pydantic v2 models. The LLM (Gemini via LangChain/LangGraph) serves purely as an intent router, query planner, and narrative synthesizer. This design completely eliminates mathematical hallucinations.

---

## 🎯 Problem Statement

Traditional CSV analysis requires users to manually inspect schemas, write Pandas transformations, and generate visualization code.

The **CSV Analytics Agent** provides a conversational workflow:

```text
User Question
     ↓
Semantic Column Retrieval (Sentence Transformers + FAISS)
     ↓
Agent Planning (LangGraph + Gemini)
     ↓
Deterministic Computation / AST Python Sandbox
     ↓
Plotly / Matplotlib Visualization
     ↓
Natural-Language Explanation & Response Normalization
```

---

## ✨ Key Features

- 📂 **CSV Dataset Upload**: Auto-detects encodings (`utf-8`, `latin-1`, `cp1252`), parses currency strings (`$1,099`), percentages (`64%`), and dates.
- 📊 **Dataset Statistical DNA**: Computes summary statistics (row/col count, missingness ratios, cardinality, quantiles) without side effects.
- 💬 **Natural Language Queries**: Interactive conversational workflow powered by Gemini and LangGraph.
- 🔎 **Semantic Column Retrieval**: Indexes column schemas into FAISS using Sentence Transformers (`all-MiniLM-L6-v2`) for schema discovery.
- 🧠 **LangGraph State Machine**: Orchestrates query routing, semantic retrieval, planning, tool calls, and explanation synthesis.
- 🔒 **Multi-Layer Python Execution Sandbox**: AST-validated Python code executor supporting isolated subprocesses (`SubprocessBackend`) or Docker containers (`DockerBackend`).
- 📈 **Interactive Visual Analytics**: Renderer-agnostic chart recommender generating interactive Plotly charts and high-res Matplotlib PNGs.
- 📋 **DataFrame & Artifact Protocol**: Structured `AgentResponse` encapsulating plain Markdown text narrative, interactive tables, charts, metrics, and download buttons.
- 🔄 **AI Response Normalizer**: Bridge service (`_clean_text_content` with `ast.literal_eval`) stripping LLM metadata (`extras`, `signature`) into clean Markdown text.
- 🧪 **Automated Testing Suite**: 475+ unit, integration, and normalization tests covering core domain components.

---

## 🏗️ Architecture

```text
                         USER
                           │
                           ▼
                     STREAMLIT UI
                           │
                           ▼
                    CSV DATASET
                           │
                           ▼
                    PANDAS DATAFRAME
                           │
                           ▼
                 DATASET PROFILING
                           │
                           ▼
                    USER QUESTION
                           │
                           ▼
                      LANGGRAPH
                           │
                           ▼
                SEMANTIC RETRIEVAL
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       Sentence Transformers          FAISS
          Embeddings              Vector Store
              │                         │
              └────────────┬────────────┘
                           ▼
                 RELEVANT COLUMNS
                           │
                           ▼
                        PLANNER
                           │
                           ▼
                  PYTHON GENERATOR
                           │
                           ▼
                    PANDAS ENGINE
                           │
                           ▼
                  VERIFIED RESULTS
                     │          │
                     ▼          ▼
              VISUALIZATION   GEMINI
                              EXPLANATION
                     │          │
                     └────┬─────┘
                          ▼
                 RESPONSE NORMALIZER
                          │
                          ▼
                    AGENT RESPONSE
                          │
                          ▼
                     STREAMLIT UI
```

---

## 🔎 Semantic Column Retrieval

The system contains a dedicated semantic retrieval layer (`src/csv_analytics_agent/memory/`):

```text
Column / Schema Text
       ↓
Sentence Transformer (all-MiniLM-L6-v2)
       ↓
Embedding Vector (384D)
       ↓
FAISS Vector Store (IndexFlatL2)
       ↓
Similarity Search
       ↓
Relevant Columns (retrieved_columns)
```

For full details on semantic retrieval, read [docs/semantic-retrieval.md](docs/semantic-retrieval.md).

---

## 🧠 AI / Agent Architecture

### Separation of Responsibilities

| Layer | Technology | Responsibility |
| :--- | :--- | :--- |
| **Semantic Retrieval** | Sentence Transformers + FAISS | Determine which dataset columns are semantically relevant |
| **LLM Orchestrator** | Google Gemini (`ChatGoogleGenerativeAI`) | Understand natural language questions, plan analysis, and explain verified results |
| **Agent Workflow** | LangGraph `StateGraph` | Manage node state transitions, iterations, and checkpointing |
| **Analytical Engine** | Pandas & NumPy | Perform deterministic numerical operations, aggregations, and statistics |
| **Security Sandbox** | AST Inspector + Docker / Subprocess | Safely execute LLM-generated Python analysis code |
| **Response Normalizer** | `result_normalizer.py` | Parse raw content blocks into plain Markdown, stripping internal metadata |
| **Presentation Layer** | Streamlit | Render text, interactive charts, DataFrames, and export buttons |

---

## 🔄 Response Normalization

When modern LLMs (such as Google Gemini via `langchain-google-genai`) return content block structures, raw representations contain internal metadata:

```python
[
    {
        "type": "text",
        "text": "The dataset contains 1,465 product records across 16 columns...",
        "extras": {
            "signature": "EI4K..."
        }
    }
]
```

The normalization pipeline strips this metadata:

```text
Raw AIMessage / Content Blocks
              ↓
  _clean_text_content() [json.loads & ast.literal_eval fallback]
              ↓
  Strip internal metadata ('extras', 'signature', 'tool_call_id')
              ↓
  Clean Markdown Answer String
              ↓
  Canonical AgentResponse Contract
              ↓
  st.markdown() UI Rendering
```

For full details on response normalization, see [docs/response-normalization.md](docs/response-normalization.md).

---

## 💬 Example Questions

| Category | Example Question | Target Capability |
| :--- | :--- | :--- |
| **Summary** | *"Give me a summary of this dataset."* | `DatasetProfiler` |
| **Aggregation** | *"What is the average rating across all products?"* | `AnalyticsEngine.aggregate` |
| **Ranking** | *"Which are the top 10 products by review count?"* | `AnalyticsEngine.top_n` |
| **Distribution** | *"Show me the distribution of product ratings."* | `VisualizationEngine` (Histogram) |
| **Filtering** | *"Find products with discounts exceeding 50%."* | `AnalyticsEngine.filter` |
| **Comparison** | *"Which product category has the highest average rating?"* | `AnalyticsEngine.groupby` + Bar Chart |
| **Relationship** | *"Is price correlated with customer ratings?"* | `VisualizationEngine` (Scatter Plot) |
| **Semantic Query** | *"Find columns related to customer satisfaction."* | Semantic FAISS Retrieval |

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **UI Framework** | Streamlit |
| **Data Processing** | Pandas & NumPy |
| **LLM Provider** | Google Gemini (`ChatGoogleGenerativeAI`) |
| **LLM Core** | LangChain Core |
| **Agent Orchestration** | LangGraph |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Vector Search** | FAISS Vector Store (`faiss-cpu`) |
| **Visualization** | Plotly & Matplotlib |
| **Sandboxing** | Subprocess / Docker (`DockerBackend`) |
| **Testing** | pytest (475 passed tests), Ruff, MyPy |

---

## 📁 Project Structure

```text
csv-analytics-agent/
│
├── src/
│   └── csv_analytics_agent/
│       ├── graph/            # LangGraph StateGraph, retrieval, planner & runtime
│       ├── memory/           # FAISS vector store, Sentence Transformers & embeddings
│       ├── execution/        # CapabilityRegistry, AnalyticsEngine, PandasProvider
│       ├── preprocessing/    # Data loading, encoding detection & coercion
│       ├── profiler/         # Column statistical DNA & profiling
│       ├── visualization/    # Chart recommendation & Plotly/Matplotlib renderers
│       ├── services/         # Result normalizer & API gateway converters
│       └── python_engine/    # AST pre-validator, subprocess & Docker sandbox
│
├── streamlit_app/            # Streamlit Multi-Page Web Application
│   ├── app.py                # Application entrypoint
│   ├── components/           # Reusable Streamlit UI components
│   └── services/             # Backend service bridge
│
├── sandbox/                  # Docker sandbox container build context
├── docs/                     # System architecture & documentation docs
│   ├── architecture.md
│   ├── langchain-langgraph.md
│   ├── semantic-retrieval.md
│   ├── response-normalization.md
│   └── interview-guide.md
│
├── tests/                    # Complete unit, integration, and memory test suite (475 passed)
├── pyproject.toml            # Project configuration (uv / hatchling)
└── README.md                 # Master GitHub README
```

---

## 🚀 Installation & Quickstart

### 1. Prerequisites
- **Python**: 3.10 or higher
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### 2. Clone & Install Dependencies

```bash
git clone https://github.com/Vishaldave45/CSV-Analytics-Agent.git
cd CSV-Analytics-Agent

uv sync
# Or using pip: pip install -e ".[dev]"
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure your API key:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
GOOGLE_API_KEY=AIzaSy_your_key_here
PYTHON_EXECUTION_BACKEND=subprocess
```

### 4. Run Application

```bash
uv run streamlit run streamlit_app/app.py
```

Open browser at `http://localhost:8501`.

---

## 🧪 Testing

```bash
# Run pytest suite
uv run pytest

# Run semantic retrieval & memory tests
uv run pytest tests/memory/ -v

# Run linting and type checks
uv run ruff check .
uv run mypy src/
```

---

## 📚 Detailed Documentation

| Document | Description |
| :--- | :--- |
| **[docs/architecture.md](docs/architecture.md)** | End-to-end system architecture and pipeline flow. |
| **[docs/semantic-retrieval.md](docs/semantic-retrieval.md)** | Sentence Transformers + FAISS vector index architecture. |
| **[docs/langchain-langgraph.md](docs/langchain-langgraph.md)** | LangGraph state machine, nodes, and LLM bindings. |
| **[docs/response-normalization.md](docs/response-normalization.md)** | Text cleaner (`_clean_text_content`) and `AgentResponse` protocol. |
| **[docs/interview-guide.md](docs/interview-guide.md)** | 30s/1m/3m technical project explanation & engineering decisions. |

---

## ⚠️ Limitations

- **In-Memory Scale**: Optimized for CSV datasets up to 1GB loaded into memory.
- **Execution Timeout**: Dynamic Python code execution is capped at 30 seconds and 512MB RAM.

---

## 🗺️ Future Roadmap

- [ ] Support Parquet, Excel (`.xlsx`), and JSON formats
- [ ] Connectors for PostgreSQL, Snowflake, and BigQuery
- [ ] Pluggable vector store backends (Chroma / Qdrant)
- [ ] MicroVM sandbox execution (gVisor / Firecracker)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.