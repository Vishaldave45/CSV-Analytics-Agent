"""JSON and HTML report generator module for CSV Analytics Agent evaluation."""

from __future__ import annotations

import datetime
import html
import json
from pathlib import Path
from typing import Any


def save_json_reports(report_data: dict[str, Any], reports_dir: Path) -> tuple[Path, Path]:
    """Save latest.json and timestamped history JSON report.

    Returns:
        Tuple of (latest_json_path, history_json_path).
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    history_dir = reports_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{timestamp_str}"
    report_data["run_id"] = run_id

    latest_path = reports_dir / "latest.json"
    history_path = history_dir / f"{run_id}.json"

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return latest_path, history_path


def load_previous_baseline(reports_dir: Path) -> dict[str, Any] | None:
    """Load latest previous history JSON report for regression comparison."""
    history_dir = reports_dir / "history"
    if not history_dir.exists():
        return None

    history_files = sorted(history_dir.glob("*.json"))
    if not history_files:
        return None

    # Pick the most recent history file before the current run (if at least 2 exist, pick second last)
    target_file = history_files[-2] if len(history_files) >= 2 else history_files[-1]
    try:
        with open(target_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def generate_html_report(data: dict[str, Any]) -> str:
    """Generate self-contained interactive HTML evaluation report."""
    meta = data.get("metadata", {})
    metrics = data.get("metrics", {})
    cases = data.get("cases", [])
    run_id = data.get("run_id", meta.get("timestamp", "N/A"))

    pass_rate = meta.get("overall_pass_rate", data.get("pass_rate", 0.0)) * 100.0
    pass_cls = "pass" if pass_rate >= 85.0 else "fail"

    cases_html: list[str] = []
    for c in cases:
        c_id = html.escape(str(c.get("case_id", "")))
        q_raw = c.get("question", "")
        q_text = html.escape(q_raw[0] if isinstance(q_raw, list) else str(q_raw))
        cat = html.escape(str(c.get("category", "")))
        passed = c.get("passed", False)
        st_badge = (
            '<span class="badge pass">✓ PASS</span>'
            if passed
            else '<span class="badge fail">❌ FAIL</span>'
        )

        tools_used = ", ".join(c.get("actual_tools", [])) or "None (Direct response)"
        lat = c.get("latency_ms", 0.0)
        reasons = "<br>".join(c.get("failures", [])) or "None"

        cases_html.append(f"""
        <tr onclick="toggleDetails('{c_id}')" style="cursor: pointer;">
            <td><code>{c_id}</code></td>
            <td><strong>{q_text}</strong></td>
            <td><span class="tag">{cat}</span></td>
            <td>{st_badge}</td>
            <td><code>{html.escape(tools_used)}</code></td>
            <td>{lat:.1f} ms</td>
        </tr>
        <tr id="details-{c_id}" class="details-row" style="display: none;">
            <td colspan="6">
                <div class="details-box">
                    <p><strong>Full Question:</strong> {q_text}</p>
                    <p><strong>Executed Tools:</strong> <code>{html.escape(tools_used)}</code></p>
                    <p><strong>Failure Trace / Notes:</strong> {html.escape(reasons)}</p>
                </div>
            </td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Analytics Agent — LLM Evaluation Report</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --pass-color: #22c55e;
            --fail-color: #ef4444;
            --warn-color: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }}
        .header h1 {{
            margin: 0 0 0.5rem 0;
            color: var(--accent-blue);
            font-size: 1.8rem;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.25rem;
            text-align: center;
        }}
        .card .value {{
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0.4rem 0;
        }}
        .card .value.pass {{ color: var(--pass-color); }}
        .card .value.fail {{ color: var(--fail-color); }}
        .card .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .progress-bar {{
            background: var(--border-color);
            border-radius: 6px;
            height: 8px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        .progress-fill {{
            background: var(--pass-color);
            height: 100%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: #1e293b;
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        tr:hover {{
            background: #334155;
        }}
        .badge {{
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge.pass {{ background: rgba(34, 197, 94, 0.2); color: var(--pass-color); }}
        .badge.fail {{ background: rgba(239, 68, 68, 0.2); color: var(--fail-color); }}
        .tag {{
            background: #334155;
            color: var(--accent-blue);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        .details-box {{
            background: #0f172a;
            padding: 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            border-left: 3px solid var(--accent-blue);
        }}
        code {{
            font-family: monospace;
            background: #0f172a;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            color: var(--accent-blue);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 CSV Analytics Agent — Evaluation Report</h1>
            <div class="meta-grid">
                <div><strong>Run ID:</strong> <code>{run_id}</code></div>
                <div><strong>Model:</strong> {html.escape(str(meta.get("model", "gemini-flash-lite-latest")))}</div>
                <div><strong>Total Cases:</strong> {meta.get("total_cases", len(cases))}</div>
                <div><strong>Timestamp:</strong> {html.escape(str(meta.get("timestamp", "")))}</div>
            </div>
        </div>

        <div class="cards-grid">
            <div class="card">
                <div class="label">Overall Pass Rate</div>
                <div class="value {pass_cls}">{pass_rate:.1f}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {pass_rate}%;"></div></div>
            </div>
            <div class="card">
                <div class="label">Router Accuracy</div>
                <div class="value pass">{metrics.get("router_accuracy", metrics.get("answer_relevance", 1.0)) * 100:.1f}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {metrics.get("router_accuracy", metrics.get("answer_relevance", 1.0)) * 100}%;"></div></div>
            </div>
            <div class="card">
                <div class="label">Planner Accuracy</div>
                <div class="value pass">{metrics.get("planner_accuracy", metrics.get("tool_selection_quality", 1.0)) * 100:.1f}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {metrics.get("planner_accuracy", metrics.get("tool_selection_quality", 1.0)) * 100}%;"></div></div>
            </div>
            <div class="card">
                <div class="label">Numerical Correctness</div>
                <div class="value pass">{metrics.get("numerical_correctness", 1.0) * 100:.1f}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {metrics.get("numerical_correctness", 1.0) * 100}%;"></div></div>
            </div>
            <div class="card">
                <div class="label">Security Pass Rate</div>
                <div class="value pass">{metrics.get("security_pass_rate", metrics.get("security", 1.0)) * 100:.1f}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {metrics.get("security_pass_rate", metrics.get("security", 1.0)) * 100}%;"></div></div>
            </div>
        </div>

        <h2>📋 Benchmark Test Cases</h2>
        <table>
            <thead>
                <tr>
                    <th>Case ID</th>
                    <th>User Question</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Executed Tools</th>
                    <th>Latency</th>
                </tr>
            </thead>
            <tbody>
                {"".join(cases_html)}
            </tbody>
        </table>
    </div>

    <script>
        function toggleDetails(id) {{
            var el = document.getElementById("details-" + id);
            if (el.style.display === "none" || el.style.display === "") {{
                el.style.display = "table-row";
            }} else {{
                el.style.display = "none";
            }}
        }}
    </script>
</body>
</html>
"""
    return html_content
