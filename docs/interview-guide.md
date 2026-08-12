# Technical Interview & Engineering Design Guide

## Project Summary

### 30-Second Elevator Pitch
> "I built an enterprise-grade CSV Analytics Agent in Python that allows users to ask natural-language questions about tabular datasets. The system uses a 'Deterministic First, LLM Second' architecture: pure Pandas and custom engines calculate 100% accurate statistical results and generate charts, while a LangGraph-orchestrated Gemini LLM handles query planning, semantic column retrieval via FAISS vector memory, and natural-language narrative explanation. Dynamic code execution runs inside a multi-layer AST-validated subprocess or Docker sandbox, and a response normalizer guarantees clean Markdown outputs."

---

## Key Technical Questions & Answers

### 1. Why use an LLM for planning but Pandas for calculation?
**Answer:** LLMs are excellent at natural language understanding and intent reasoning, but unreliable at performing multi-step mathematical calculations in memory. By separating intent planning from execution, the LLM determines *what* needs to be calculated, while Pandas executes the math deterministically. This eliminates numerical hallucinations completely.

### 2. How did you prevent the LLM from executing malicious code in the Python Sandbox?
**Answer:** We implemented a multi-layered defense-in-depth model in `python_engine`:
1. **AST Static Code Inspection**: Prior to execution, the code's Abstract Syntax Tree is inspected using `_SecurityASTVisitor`. We explicitly reject forbidden imports (`os`, `sys`, `subprocess`), dangerous builtins (`exec`, `eval`), and reflection (`__subclasses__`).
2. **Environment Stripping**: API keys and environment variables are purged from the execution context.
3. **Container Isolation**: In container mode (`DockerBackend`), execution runs inside an unprivileged, non-root Docker container (`--user 1000:1000`) with read-only root filesystems, resource limits (512MB RAM, 1 CPU), and disabled network access (`--network none`).

### 3. What caused the raw `[{'type': 'text', ...}]` bug in the UI and how was it solved?
**Answer:** Modern LangChain Google Gemini bindings return content as a list of content-block dictionaries (containing `extras` and `signature` metadata). Originally, stringifying `msg.content` directly converted the list object into a literal Python string representation. We resolved this by building a dedicated response normalization layer (`_clean_text_content` in `result_normalizer.py`) that recursively parses content blocks and single-quoted Python repr strings (`ast.literal_eval`), extracting pure Markdown text into a canonical `AgentResponse` contract before rendering.

---

## Technical Concept Mapping

| System Requirement | Component / Module | Technology / Pattern |
| :--- | :--- | :--- |
| Intent Routing | `graph/router.py` | LLM Intent Classification & Fallback Node |
| Semantic Memory | `memory/` | FAISS Vector Store + SentenceTransformers |
| State Management | `graph/state.py` | LangGraph StateGraph + InMemory Checkpointing |
| Deterministic Execution | `execution/` | Strategy Pattern + CapabilityRegistry |
| Code Sandboxing | `python_engine/` | AST Inspection + Docker / Subprocess Isolation |
| Output Normalization | `services/result_normalizer.py` | Recursive Block Extractor + Pydantic v2 |
| UI Presentation | `streamlit_app/` | Multi-Page Streamlit + Custom Glassmorphism CSS |
