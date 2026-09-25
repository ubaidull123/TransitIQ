from datetime import datetime, timezone
from typing import Any

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


def _perform_analysis(
    exception_type: str,
    severity: str,
    missing_information: list[str],
    recommended_actions: list[str],
    runtime: ToolRuntime,
    create_actions: bool,
) -> Command:
    state = runtime.state or {}
    existing_history = list(state.get("analysis_history") or [])
    analysis_record = {
        "exception_type": exception_type,
        "severity": severity,
        "missing_information": missing_information,
        "recommended_actions": recommended_actions,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    updated_history = [*existing_history, analysis_record]

    existing_actions = list(state.get("actions") or [])
    start_idx = len(existing_actions) + 1
    new_actions = [
        {
            "id": f"ACT-{start_idx + i}",
            "description": action_desc.strip(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
        for i, action_desc in enumerate(recommended_actions)
        if create_actions and not existing_history and action_desc.strip()
    ]
    all_actions = [*existing_actions, *new_actions]
    new_status = "action_required" if all_actions else "analyzed"

    msg = (
        f"Analysis complete for shipment {state.get('shipment_id')}.\n"
        f"Classification: {exception_type} (Severity: {severity})\n"
        f"Missing info: {missing_information}\n"
        f"Actions created: {[a['id'] for a in new_actions]}"
    )

    return Command(
        update={
            "exception_type": exception_type,
            "severity": severity,
            "missing_information": missing_information,
            "recommended_actions": recommended_actions,
            "latest_analysis": analysis_record,
            "actions": all_actions,
            "analysis_history": updated_history,
            "status": new_status,
            "current_step": "done",
            "messages": [ToolMessage(content=msg, tool_call_id=runtime.tool_call_id)],
        }
    )


@tool
def analyze_case(
    exception_type: str,
    severity: str,
    missing_information: list[str],
    recommended_actions: list[str],
    runtime: ToolRuntime,
) -> Command:
    """Analyze the shipment issue, determine classification, severity, missing info, and recommended actions.
    This tool persists the structured analysis into analysis_history, creates operational actions, and sets case status.
    """
    return _perform_analysis(
        exception_type=exception_type,
        severity=severity,
        missing_information=missing_information,
        recommended_actions=recommended_actions,
        runtime=runtime,
        create_actions=True,
    )


@tool
def reanalyze_case(
    exception_type: str,
    severity: str,
    missing_information: list[str],
    recommended_actions: list[str],
    runtime: ToolRuntime,
) -> Command:
    """Re-analyze a case after new context or information has been received.
    Appends the new analysis run to analysis_history without overwriting previous runs.
    """
    return _perform_analysis(
        exception_type=exception_type,
        severity=severity,
        missing_information=missing_information,
        recommended_actions=recommended_actions,
        runtime=runtime,
        create_actions=False,
    )

@tool
def get_analysis_history(runtime: ToolRuntime) -> list[dict[str, Any]]:
    """Retrieve the complete analysis history list directly from active state."""
    state = runtime.state or {}
    return list(state.get("analysis_history") or [])