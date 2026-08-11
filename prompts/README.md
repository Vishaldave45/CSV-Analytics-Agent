# CSV Analytics Agent — Prompt Registry

This directory contains the canonical static prompt instruction templates (`.md` files) used across the CSV Analytics Agent workflow layers.

## Structure

```text
prompts/
├── README.md                 # Registry documentation & input/output contracts
├── shared/
│   ├── grounding.md          # Dataset as single source of truth rules
│   ├── security.md           # Untrusted CSV data isolation rules
│   └── data_quality.md       # Data quality & coercion handling guidelines
├── router/
│   └── system.md             # Intent classification rules
├── planner/
│   └── system.md             # Tool selection & minimum execution plan rules
├── python/
│   ├── system.md             # Vectorized Python code generation rules
│   └── security.md           # Python sandbox execution boundary rules
├── visualization/
│   └── system.md             # Visualization chart recommendation rules
├── response/
│   ├── system.md             # Narrative response synthesis rules
│   └── evidence.md           # Provenance & evidence formatting guidelines
└── followup/
    └── system.md             # Conversational reference resolution rules
```

## Prompt Modules & Responsibilities

| Layer | Files | Inputs | Responsibilities |
|-------|-------|--------|------------------|
| **Shared** | `grounding.md`, `security.md`, `data_quality.md` | N/A | Foundational safety, grounding, and quality principles composed into downstream layer prompts. |
| **Router** | `router/system.md` | `user_question` | Classifies user intent into canonical categories (`chitchat`, `dataset_metadata`, `analytical`, `visualization`, `clarification`, `unsupported`, `reset`, `meta`). |
| **Planner** | `planner/system.md` | `row_count`, `column_descriptions`, `active_filters_summary` | Selects minimum valid execution tools (`aggregate`, `group`, `filter`, `top_n`, `sort`, `describe`, `render_visualization`, `python_analysis`). |
| **Python** | `python/system.md`, `python/security.md` | `schema_summary`, `retrieved_columns_summary`, `additional_context` | Generates safe Python pandas code assigning answer to `result`. |
| **Visualization** | `visualization/system.md` | `profile`, `insights` | Maps data relationships to optimal chart types (Plotly / images). |
| **Response** | `response/system.md`, `response/evidence.md` | `question`, `verified_result`, `evidence` | Synthesizes user-facing answers from verified results without altering numbers or inventing facts. |
| **Follow-up** | `followup/system.md` | `messages`, `active_filters` | Resolves conversational pronouns (`it`, `its`, `that`, `the highest category`). |
