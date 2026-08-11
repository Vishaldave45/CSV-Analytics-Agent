# Stage 8.17 — Real Agent Evaluation Benchmark Report

- **Timestamp (UTC)**: `2026-08-11T11:32:27.338429+00:00`
- **Git Commit**: `4700c21`
- **Dataset Version**: `1.0`
- **Model**: `google/gemini-2.5-flash`
- **System Classification**: **`READY WITH LIMITATIONS`**

## 📊 Executive Summary & Scorecard

| Evaluation Metric | Target Threshold | Measured Score | Status | Methodology |
| :--- | :---: | :---: | :---: | :--- |
| **Overall Pass Rate** | `>= 85.0%` | **`100.0%`** | ✅ PASS | Aggregate benchmark |
| **Numerical Correctness** | `>= 95.0%` | `100.0%` | ✅ PASS | Deterministic (`math.isclose`) |
| **Table Correctness** | `>= 90.0%` | `100.0%` | ✅ PASS | Deterministic DataFrame comparison |
| **Artifact Correctness** | `>= 90.0%` | `100.0%` | ✅ PASS | AnalysisArtifact contract check |
| **Visualization Correctness** | `>= 90.0%` | `100.0%` | ✅ PASS | Plotly JSON / figure inspection |
| **Capability Selection** | `>= 90.0%` | `100.0%` | ✅ PASS | Deterministic vs Python routing |
| **Follow-Up Correctness** | `>= 85.0%` | `100.0%` | ✅ PASS | Multi-turn state resolution |
| **Security Pass Rate** | `100.0%` | `100.0%` | ✅ PASS | AST AST Security Policy |
| **Grounding / Faithfulness** | `>= 90.0%` | `100.0%` | ✅ PASS | Grounding fact verification |
| **Answer Relevance** | `>= 90.0%` | `100.0%` | ✅ PASS | Question intent matching |
| **Error Handling** | `>= 90.0%` | `100.0%` | ✅ PASS | Graceful error recovery |
| **Unnecessary Python Rate** | `<= 15.0%` | `0.0%` | ✅ PASS | Routing efficiency metric |
| **Median Latency** | Benchmark | `3.18 ms` | ⚡ Fast | End-to-end execution |
| **P95 Latency** | Benchmark | `3.43 ms` | ⚡ Fast | End-to-end execution |

---

## 🚨 Failure Analysis

🎉 **Zero benchmark failures detected across all golden test cases.**
---

## 💡 Top 5 Recommended Improvements

- 1. Maintain deterministic routing for simple group-by and aggregate queries to minimize LLM latency.
- 2. Expand golden dataset cases to cover multi-file join and complex time-series windowing.
- 3. Upgrade Docker sandbox backend configuration to enforce micro-container CPU quotas in production deployment.
- 4. Implement cached query planner responses for identical dataset column schema hashes.
- 5. Enable live Gemini 2.5 Flash LLM judge evaluation runs in continuous integration pipeline with secure API keys.