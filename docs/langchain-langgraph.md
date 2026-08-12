# LangChain Core and LangGraph Workflow Architecture

## Overview

The CSV Analytics Agent uses **LangChain Core** for component abstractions (messages, tools, prompts, LLM bindings) and **LangGraph** for workflow state-machine orchestration.

| Technology | Layer | Purpose |
| :--- | :--- | :--- |
| **LangChain Core** | Abstraction Layer | Defines `AIMessage`, `HumanMessage`, `StructuredTool`, and prompt templates. |
| **Google GenAI Integration** | Model Layer | `ChatGoogleGenerativeAI` binding for Gemini reasoning and tool calling. |
| **LangGraph** | Workflow Engine | `StateGraph` managing node state transitions, state checkpointing, and tool execution loops. |

---

## LangGraph Node Pipeline

```text
                  START
                    │
                    ▼
               Router Node (Intent Classification)
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
Chitchat / Clarification    Analytical Query
       │                         │
       ▼                         ▼
  Final Output            Retrieval Node (FAISS Search)
                                 │
                                 ▼
                          Planner Node (LLM Tool Choice)
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
            Tool Execution Node        Synthesizer / Explainer
            (Pandas / Sandbox)                 │
                   │                           ▼
                   └─────► Planner Loop       END
```

---

## Graph Nodes & Responsibilities

### 1. Router Node (`graph/router.py`)
Classifies input query intent (`ANALYTICAL`, `CLARIFICATION`, `CHITCHAT`, `UNSUPPORTED`).

### 2. Retrieval Node (`graph/retrieval.py`)
Queries `MemoryService` using Sentence Transformers and FAISS to populate `state["retrieved_columns"]`.

### 3. Planner Node (`graph/planner.py`)
Invokes Gemini bound with tool capabilities (`AnalyticsEngine`, `VisualizationEngine`, `PythonAnalysisTool`), evaluating whether further analysis is required.

### 4. Tool Execution Node (`graph/tool_node.py`)
Executes requested tools against Pandas or the sandboxed Python execution engine (`SubprocessBackend` / `DockerBackend`), appending `AnalysisResult` to state.

### 5. Explainer Node (`graph/explainer.py`)
Synthesizes verified Pandas calculation outputs into clean natural language Markdown text narrative.

---

## State Schema (`AgentState`)

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    dataset_name: str
    dataset_profile: dict[str, Any]
    retrieved_columns: list[str]
    last_analysis_result: dict[str, Any] | None
    router_decision: dict[str, Any] | None
    iteration_count: int
```

The `retrieved_columns` array ensures that down-stream tool execution and code generation receive explicit schema context.
