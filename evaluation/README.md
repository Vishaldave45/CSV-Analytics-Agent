# 🔬 Stage 8.10 Advanced Agent Quality & LLM Evaluation Architecture

This directory houses the isolated **AI Quality & LLM Evaluation Layer** for the **CSV Analytics Agent**.

It separates **deterministic software engineering tests** (`pytest`) from **probabilistic AI behavior evaluations** (`DeepEval`, `LangSmith`, `Promptfoo`).

```text
                    CSV AI AGENT
                         │
              ┌──────────┴──────────┐
              │                     │
       SOFTWARE TESTING        AI EVALUATION
              │                     │
           pytest             Golden Dataset
              │                     │
      ┌───────┼───────┐             │
      ▼       ▼       ▼             ▼
     Unit  Integration Security   Agent Run
                                      │
                           ┌──────────┼──────────┐
                           ▼          ▼          ▼
                       DeepEval   LangSmith  Promptfoo
                           │          │          │
                           ▼          ▼          ▼
                       Quality     Traces     Regression
```

---

## 🎯 Key Metrics Evaluated

1. **Tool Selection Quality (Deterministic vs Python Routing)**:
   - Verifies whether basic queries (e.g. `What is total revenue?`) correctly use the deterministic `AnalyticsEngine` capability.
   - Penalizes **unnecessary Python execution** to preserve deterministic engine performance and reliability.
   - Ensures custom requests (e.g. `Calculate 7-day rolling average`) correctly invoke `python_analysis`.
2. **Numerical Correctness**:
   - Evaluated deterministically via `math.isclose(actual, expected, rel_tol=1e-3, abs_tol=1e-3)`. No LLM judge is used for simple arithmetic.
3. **Artifact Semantics & Payload Structure**:
   - Validates that `TABLE`, `SCALAR`, `INTERACTIVE` (Plotly), `IMAGE`, and `FILE` artifacts match expected output structures.
4. **Dataset Grounding & Faithfulness**:
   - Evaluated via `StructuredLLMJudge` and `MissingDataExplanationEvaluator` to ensure the agent does not hallucinate unavailable columns (e.g., profit when only revenue exists).
5. **Multi-Turn Follow-Up Retention**:
   - Tests thread session context retention across multi-turn prompts (`it`, `that`, `highest category`).
6. **Security Rejection**:
   - Ensures adversarial requests (`.env` file access, shell execution) are rejected safely without system compromises.

---

## 💻 Documented Evaluation Commands

### 1. Core Software Tests (Deterministic pytest)
```bash
# Run deterministic unit and integration test suite (offline)
uv run pytest -m "not llm and not docker"
```

### 2. Master Quality Evaluation Runner
```bash
# Run complete golden dataset evaluation suite
uv run python -m evaluation.runner

# Filter by category or case ID
uv run python -m evaluation.runner --category grouping
uv run python -m evaluation.runner --case-id basic_001
```
*Outputs generated: `evaluation/reports/latest.json` & `evaluation/reports/latest.md`.*

### 3. DeepEval Quality Metrics (Optional)
```bash
# Run optional DeepEval metrics suite (AnswerRelevancy, Faithfulness)
uv run python -m evaluation.deepeval.deepeval_runner
```

### 4. LangSmith Online Trace Evaluation (Optional)
```bash
# Associate golden dataset traces with LangSmith platform (requires LANGSMITH_API_KEY)
uv run python -m evaluation.langsmith.langsmith_eval
```

### 5. Promptfoo Prompt Regression (Optional)
```bash
# Execute Promptfoo prompt regression suite
npx promptfoo eval -c evaluation/promptfoo/promptfooconfig.yaml
```

---

## 🔒 Security & Sanitization
All evaluation reports generated under `evaluation/reports/` (`latest.json` and `latest.md`) are sanitized. API keys (`GOOGLE_API_KEY`, `LANGCHAIN_API_KEY`) and private filesystem secrets are automatically redacted before saving reports.
