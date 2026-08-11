# Stage 8.14 — Verified Findings & Fixes Report

This document details every confirmed **P0**, **P1**, and **P2** finding identified during codebase audit and Stage 8.13 verification, along with the precise root cause, architectural fix, regression test path, and empirical verification results.

---

## 1. Confirmed P0 Findings & Fixes

### P0-1 & P0-3: Unsafe Thread-State Serialization & Lock Contention in Checkpointer
- **File:** [src/csv_analytics_agent/graph/checkpoint.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/graph/checkpoint.py)
- **Root Cause:** Legacy `SqliteSaver` used raw Python `pickle.dumps` for state serialization (which is insecure and fragile across python version upgrades) and lacked thread locking around open SQLite database connection calls, leading to potential multi-threading lock contention under Streamlit.
- **Implemented Fix:** Upgraded `SqliteSaver` to use native `langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer` (`serde.dumps_typed` and `serde.loads_typed`) and introduced a reentrant `threading.Lock()` across schema initialization, tuple fetching, write persistence, list operations, and thread deletions.
- **Regression Test:** `test_sqlite_saver_operations` in [tests/graph/test_runtime.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/graph/test_runtime.py).
- **Verification:** Verified save (`put`), load (`get_tuple`), list (`list`), put_writes (`put_writes`), resume, thread reset, and thread deletion (`delete_thread`) across multiple isolated thread IDs.

### P0-4: Missing Gemini API Key Handled via Dummy Credential Fallback
- **File:** [src/csv_analytics_agent/llm/gemini.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/llm/gemini.py)
- **Root Cause:** `_build_llm_instance()` previously defaulted a missing `google_api_key` to `"DUMMY_KEY_FOR_MOCKING"`, causing unhandled 400 `INVALID_ARGUMENT` errors from external API endpoints instead of failing fast during initial setup.
- **Implemented Fix:** Defined `GeminiAPIKeyError(ValueError)` and updated `_build_llm_instance()` to raise `GeminiAPIKeyError` immediately if `self._api_key` is empty/missing.
- **Regression Test:** `test_gemini_missing_api_key_raises_error` in [tests/llm/test_gemini.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/llm/test_gemini.py).
- **Verification:** `GeminiLLM(api_key=None)` correctly raises `GeminiAPIKeyError` without exposing secrets or sending dummy credentials.

---

## 2. Confirmed P1 Findings & Fixes

### P1-1: AgentRuntime.reset Inappropriately Sent Prompt String to LLM
- **File:** [src/csv_analytics_agent/graph/runtime.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/graph/runtime.py)
- **Root Cause:** `AgentRuntime.reset()` previously invoked `self.run("reset")`, which sent the string `"reset"` as a user prompt to the LLM agent model.
- **Implemented Fix:** Refactored `reset()` to bypass LLM generation, invoke `reset_node()` to reset initial channel state directly, and store the reset state in `self._checkpointer.put(...)`.
- **Regression Test:** `test_agent_runtime_reset` in [tests/graph/test_runtime.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/graph/test_runtime.py).
- **Verification:** Confirmed conversation history and active filters are cleared directly in memory and checkpointer without executing LLM generation calls.

### P1-2: Router Node Output Compatibility
- **File:** [src/csv_analytics_agent/graph/router.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/graph/router.py) & [build.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/graph/build.py)
- **Root Cause:** `router_node` returned a Pydantic `RouterDecision` object directly.
- **Implemented Fix:** Updated `route_after_router` in `build.py` to evaluate `RouterDecision`, `dict`, and `AgentState` metadata structures interchangeably.
- **Regression Test:** `test_router_new_query` in [tests/graph/test_router.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/graph/test_router.py).
- **Verification:** All router decision tests pass cleanly with 100% route accuracy.

### P1-4: Subprocess Execution Modifies Discarded DataFrame Copy
- **File:** [src/csv_analytics_agent/python_engine/backends.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/python_engine/backends.py)
- **Root Cause:** When user code modified `df` in dynamic Python execution (e.g. `df = df[df['sales'] > 10]`), the mutated DataFrame was not captured as a distinct artifact payload.
- **Implemented Fix:** Updated `RUNNER_SCRIPT_CONTENT` to compare `user_globals["df"]` with original `dataset.csv`. If mutated, captures a `dataframe` artifact named `"df"` with `metadata: {"mutated": True}`.
- **Regression Test:** `test_subprocess_backend_mutated_dataframe_artifact` in [tests/python_engine/test_backends.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/python_engine/test_backends.py).
- **Verification:** Verified `test_subprocess_backend_mutated_dataframe_artifact` passes.

### P1-5: FAISS Distance Metric Normalization
- **File:** [src/csv_analytics_agent/memory/faiss_store.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/src/csv_analytics_agent/memory/faiss_store.py)
- **Root Cause:** Raw FAISS L2 squared distance was returned directly as `score` without normalizing to a bounded similarity metric.
- **Implemented Fix:** Converted distance to bounded similarity score $S = \frac{1}{1 + d^2} \in (0, 1]$.
- **Regression Test:** `test_faiss_store_search_ordering` in [tests/memory/test_faiss_store.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/memory/test_faiss_store.py).
- **Verification:** Identical vectors yield $S = 1.0$; closer vectors produce higher similarity scores.

---

## 3. Confirmed P2 Findings & Fixes

### P2-1: Unused Mypy Configuration Sections
- **File:** [mypy.ini](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/mypy.ini)
- **Root Cause:** `mypy.ini` contained unused configuration section `[mypy-streamlit.*]`.
- **Implemented Fix:** Removed unused section.
- **Regression Test:** `uv run mypy src`.
- **Verification:** `mypy src` passes with zero warnings or unused section errors.

### P2-2: Evaluation Framework Synthetic Result Dependency
- **File:** [evaluation/runner.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/evaluation/runner.py) & [tests/evaluation/runner.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/evaluation/runner.py)
- **Root Cause:** `MasterEvaluationRunner` previously generated synthetic `AnalysisResult` objects instead of using actual results from `AgentRuntime`.
- **Implemented Fix:** Updated evaluation runner to capture real `AnalysisResult` from `AgentRuntime` and pass it directly to all evaluators.
- **Regression Test:** `test_evaluator_consumes_real_agent_result` in [tests/evaluation/test_golden_questions.py](file:///home/vishal-dave/Desktop/AI-ML/csv-analytics-agent/tests/evaluation/test_golden_questions.py).
- **Verification:** Evaluators process real agent execution output end-to-end.

---

## 4. Key Invariant Verification Summary

1. **Python Single Execution Invariant:** Verified generator calls = 1, executor calls = 1 per request (`test_single_generation_and_execution_count`).
2. **Sandbox Invariant:** AST validation blocks dangerous imports, filesystem access, subprocess, networking, eval/exec, and dangerous builtins. Clear distinction documented between subprocess (process-level AST filtering) and container (true Docker sandbox).
3. **LLM Context Invariant:** Unrestricted DataFrames are never sent to LLM. Tool outputs are summarized to `row_count`, `column_count`, `columns`, and top 10 preview. Verified bounded serialization size (< 50 KB) for 10,000 x 50 DataFrames (`test_large_dataframe_tool_output_bounding`).
4. **Evaluation Invariant:** Evaluation flow is `GoldenCase → REAL AgentRuntime → REAL AnalysisResult → Evaluation`. Zero synthetic `AnalysisResult` creation remains in `evaluation/`.
5. **Checkpoint Invariant:** Tested save, load, list, resume, reset, delete_thread across multiple isolated thread IDs.
6. **Runtime Configuration:** `model_name`, `temperature`, `max_iterations` pass through `AgentRuntime` cleanly (`test_runtime_configuration_passthrough`).
7. **Security / Secrets:** Confirmed `.env`, `*.db`, and secrets are excluded from git tracking (`git ls-files` check passed cleanly).
8. **Follow-Up Context:** Follow-ups are rule-driven and generic; category references resolve via state context.
9. **Artifact Contract:** Both deterministic and Python execution paths produce standard `AnalysisResult` with `AnalysisArtifact[]`.
10. **Frontend-Backend Boundary:** Core `src/` has zero dependencies on `streamlit`.
