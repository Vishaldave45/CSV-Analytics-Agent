"""Service layer to normalize internal AgentState into canonical UI AgentResponse."""

from __future__ import annotations

import ast
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.graph.checkpoint import AnalysisResultCheckpoint
from csv_analytics_agent.graph.router import RouterIntent
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.models.response import AgentResponse, AgentResponseType
from csv_analytics_agent.results.models import AnalysisArtifact


def _extract_last_ai_message(messages: list[BaseMessage]) -> str:
    """Extract the last non-tool-payload AI message from state."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            content = str(msg.content or "")
            if content.startswith("{") and ("'shape'" in content or "'columns'" in content):
                continue
            return content.strip()
    return ""


def _extract_insights(messages: list[BaseMessage]) -> list[str]:
    """Attempt to parse insights from the last AI message if structured, or return empty."""
    # (Placeholder) In a more advanced implementation, the AI message could be
    # generated as JSON by the explainer to strictly separate 'answer' and 'insights'.
    # For now, we return empty insights as we rely on 'answer'.
    return []


def _safe_eval_dict(val: Any) -> dict[str, Any] | None:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.startswith("{"):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return None


def normalize_state_to_response(state: AgentState) -> AgentResponse:
    """Convert raw internal AgentState into a canonical, safe AgentResponse."""
    messages = state.get("messages", [])
    router_decision = _safe_eval_dict(state.get("router_decision"))
    intent = router_decision.get("intent") if router_decision else None

    answer = _extract_last_ai_message(messages)

    # 1. Handle Domain Errors & Clarifications via Router Decision
    if intent == RouterIntent.CLARIFICATION.value:
        return AgentResponse(
            type=AgentResponseType.CLARIFICATION,
            answer=answer or "Could you please clarify your request?",
            suggestions=[
                "Top 5 products by revenue",
                "Show revenue over time",
                "Summarize the dataset",
            ],
        )
    elif intent in (
        RouterIntent.CHITCHAT.value,
        RouterIntent.META.value,
        RouterIntent.UNSUPPORTED.value,
    ):
        return AgentResponse(
            type=AgentResponseType.TEXT,
            answer=answer,
        )

    # 2. Extract Artifacts from last_analysis_result
    last_res: dict[str, Any] | AnalysisResultCheckpoint | None = state.get("last_analysis_result")

    # Check for direct pipeline failures (Domain exceptions caught in runtime)
    # The caller (backend.py) may set a custom metadata tag for error.

    if not last_res:
        # If there's no result but we have an answer, it's just a text response.
        # Check if there is an explicit error message in the text.
        if "⚠️" in answer or "Something went wrong" in answer:
            return AgentResponse(
                type=AgentResponseType.ERROR,
                error=answer,
                answer="I couldn't complete that analysis.",
            )

        return AgentResponse(
            type=AgentResponseType.TEXT,
            answer=answer or "No analytical result was generated.",
        )

    # Handle AnalysisResult dict structure
    status = (
        last_res.get("status", "success")
        if isinstance(last_res, dict)
        else getattr(last_res, "status", "success")
    )
    narrative = (
        last_res.get("narrative", "")
        if isinstance(last_res, dict)
        else getattr(last_res, "narrative", "")
    )

    status_val = getattr(status, "value", str(status))
    if str(status_val).lower() in ("failed", "error") or "failed" in str(status_val).lower():
        err_msg = (
            last_res.get("error_message", narrative)
            if isinstance(last_res, dict)
            else getattr(last_res, "error_message", narrative)
        )
        return AgentResponse(
            type=AgentResponseType.ERROR,
            error=str(err_msg),
            answer="I couldn't complete that analysis.",
            calculation=f"Engine failed: {str(err_msg)}",
        )

    artifacts_raw = (
        last_res.get("artifacts", [])
        if isinstance(last_res, dict)
        else getattr(last_res, "artifacts", [])
    )

    table_artifact: AnalysisArtifact | None = None
    viz_artifact: AnalysisArtifact | None = None

    for art_raw in artifacts_raw:
        # Convert dict to model if necessary
        if isinstance(art_raw, dict):
            # Map artifact type string to Enum safely
            try:
                art = AnalysisArtifact(**art_raw)
            except Exception:
                continue
        else:
            art = art_raw

        art_type_str = str(art.artifact_type.value).lower()
        if art_type_str in ("table", "dataframe", "scalar"):
            if not table_artifact:
                table_artifact = art
        elif art_type_str in ("interactive", "image", "diagram"):
            if not viz_artifact:
                viz_artifact = art

    # Determine final type
    res_type = AgentResponseType.TEXT
    if table_artifact and viz_artifact:
        res_type = AgentResponseType.TABLE_AND_CHART
    elif table_artifact:
        res_type = AgentResponseType.TABLE
    elif viz_artifact:
        res_type = AgentResponseType.CHART

    # Ensure answer falls back to narrative if LLM didn't generate one
    final_answer = answer if answer else (str(narrative) if narrative else "Analysis complete.")

    # Extract executed tools for calculation metadata
    executed = state.get("executed_tools", [])
    calc_str = f"Tools used: {', '.join(executed)}" if executed else None

    # Empty result logic
    if table_artifact and table_artifact.payload:
        payload = table_artifact.payload
        if isinstance(payload, dict) and payload.get("row_count") == 0:
            final_answer = "No matching records found."
            calc_str = "Filter applied, but 0 rows matched."

    return AgentResponse(
        type=res_type,
        answer=final_answer,
        table=table_artifact,
        visualization=viz_artifact,
        calculation=calc_str,
        metadata={
            "iteration_count": state.get("iteration_count", 1),
            "executed_tools": executed,
        },
    )


__all__ = ["normalize_state_to_response"]
