# Semantic Column Retrieval

## Overview

The **CSV Analytics Agent** implements semantic column schema retrieval using:

- **Sentence Transformers** (`all-MiniLM-L6-v2`)
- **FAISS Vector Store** (`IndexFlatL2`)
- **`MemoryService`**
- **LangGraph Retrieval Node** (`retrieval_node`)

The purpose is to identify dataset columns that are semantically relevant to a user's natural-language question prior to analytical planning.

---

## Architecture

```text
User Question
      ↓
Sentence Transformer (all-MiniLM-L6-v2)
      ↓
Query Embedding (384-dimensional vector)
      ↓
FAISS Index (IndexFlatL2)
      ↓
Nearest-Neighbor Similarity Search
      ↓
MemorySearchResult
      ↓
Relevant Column Schemas
      ↓
LangGraph State (retrieved_columns)
```

---

## Embedding Model & Vector Index

The project implements `SentenceTransformerEmbeddings` (`src/csv_analytics_agent/memory/faiss_store.py`).

- **Default Model**: `all-MiniLM-L6-v2`
- **Embedding Dimension**: 384
- **Vector Index**: `faiss.IndexFlatL2(dimension)`

Scores returned by FAISS nearest-neighbor L2 search are converted into normalized similarity scores before being attached to the `retrieved_columns` list in the LangGraph state.

---

## Storage & Retrieval Flow

### Schema Storage Phase
When a dataset is uploaded or loaded:
1. Column metadata and descriptions are passed to `MemoryService.store()`.
2. Text is vectorized into 384-dimensional embeddings.
3. Records are persisted to `FaissVectorStore` index files on disk.

### Retrieval Phase
When a query is processed by LangGraph:
1. `retrieval_node` receives the user question.
2. `MemoryService.retrieve()` executes similarity search against FAISS.
3. Top-K relevant column schemas are attached to state as `retrieved_columns`.
4. Downstream planner (`planner_node`) and Python code generator (`python_generator.py`) receive `retrieved_columns` context.

---

## Why Semantic Retrieval for Tabular Data?

Exact string matching fails when user terminology differs from the actual dataset column name.

Example:
- **User Query**: *"What is the average income?"*
- **Dataset Column**: `annual_salary`

Semantic retrieval uses vector embeddings to map *"income"* to `annual_salary`, ensuring the LLM Planner and Python code generator select the correct column.

---

## Important Architectural Distinction

FAISS is used strictly for **semantic column retrieval**, not for performing numerical CSV analysis.

- **FAISS / Sentence Transformers**: Identifies *which* columns are semantically relevant.
- **Pandas Engine**: Performs *what* is computed (aggregations, stats, filters).
- **Gemini LLM**: Synthesizes *how* verified numerical results are explained.
