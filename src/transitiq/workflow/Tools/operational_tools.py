import ast
from datetime import datetime, timezone
import re
from typing import Any
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

VALID_ACTION_STATUSES = {"pending", "in_progress", "completed", "cancelled"}
VALID_CASE_STATUSES = {"new", "analyzed", "action_required", "in_progress", "resolved", "closed"}


def _perform_analysis(
    exception_type: str,
    severity: str,
    missing_information: list[str],
    recommended_actions: list[str],
    runtime: ToolRuntime,
    create_actions: bool,
) -> Command:
    """Core logic to analyze or re-analyze a shipment exception case."""
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
def add_context(source: str, content: str, runtime: ToolRuntime) -> Command:
    """Add chronological operational context or external updates to the shipment case.

    Args:
        source: Origin of the context (e.g., 'operator', 'carrier', 'customs_broker', 'warehouse').
        content: The factual information or update to add.
    """
    state = runtime.state or {}
    existing_context = list(state.get("context") or [])
    new_entry = {
        "source": source.strip(),
        "content": content.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    updated_context = [*existing_context, new_entry]

    return Command(
        update={
            "context": updated_context,
            "messages": [
                ToolMessage(
                    content=f"Added case context from '{source}': {content}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool
def get_case(runtime: ToolRuntime) -> dict[str, Any]:
    """Retrieve the current full shipment case state directly from active state."""
    state = runtime.state or {}
    return {
        "shipment_id": state.get("shipment_id"),
        "origin": state.get("origin"),
        "destination": state.get("destination"),
        "carrier": state.get("carrier"),
        "issue_description": state.get("issue_description"),
        "status": state.get("status", "new"),
        "current_step": state.get("current_step", "new"),
        "exception_type": state.get("exception_type"),
        "severity": state.get("severity"),
        "missing_information": state.get("missing_information", []),
        "recommended_actions": state.get("recommended_actions", []),
        "latest_analysis": state.get("latest_analysis"),
        "context": state.get("context", []),
        "actions": state.get("actions", []),
        "analysis_history": state.get("analysis_history", []),
    }


@tool
def get_analysis_history(runtime: ToolRuntime) -> list[dict[str, Any]]:
    """Retrieve the complete analysis history list directly from active state."""
    state = runtime.state or {}
    return list(state.get("analysis_history") or [])


@tool
def get_actions(runtime: ToolRuntime) -> list[dict[str, Any]]:
    """Retrieve all operational actions associated with this shipment case directly from active state."""
    state = runtime.state or {}
    return list(state.get("actions") or [])


def _parse_action_ids(action_id: Any, all_available_ids: list[str]) -> list[str]:
    """Normalize action_id into a list of uppercase action ID strings."""
    if isinstance(action_id, (list, tuple, set)):
        result = []
        for item in action_id:
            result.extend(_parse_action_ids(item, all_available_ids))
        return result

    raw = str(action_id).strip()
    if not raw:
        return []

    # Check for 'all' or '*'
    if raw.lower() in {"all", "*"}:
        return list(all_available_ids)

    # Check if raw is a bracketed representation: e.g. "['ACT-1', 'ACT-2']"
    if (raw.startswith("[") and raw.endswith("]")) or (raw.startswith("(") and raw.endswith(")")):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, (list, tuple, set)):
                return _parse_action_ids(list(parsed), all_available_ids)
        except Exception:
            pass
        cleaned = re.sub(r"[\[\]\(\)\'\"]", "", raw)
        return [part.strip().upper() for part in cleaned.split(",") if part.strip()]

    # Check if comma-separated: "ACT-1, ACT-2"
    if "," in raw:
        return [part.strip().upper() for part in raw.split(",") if part.strip()]

    return [raw.upper()]


@tool
def update_action(action_id: str | list[str], status: str, runtime: ToolRuntime) -> Command:
    """Update the status of one or multiple action items.

    Args:
        action_id: The ID of the action (e.g., 'ACT-1'), a list of IDs (['ACT-1', 'ACT-2']),
                   comma-separated IDs ('ACT-1, ACT-2'), or 'all' to update all actions.
        status: The new status ('pending', 'in_progress', 'completed', 'cancelled').
    """
    target_status = status.lower().strip()
    if target_status not in VALID_ACTION_STATUSES:
        raise ValueError(
            f"Invalid action status '{status}'. Must be one of: {sorted(VALID_ACTION_STATUSES)}"
        )

    state = runtime.state or {}
    actions = list(state.get("actions") or [])
    available_ids = [a.get("id", "").upper() for a in actions if a.get("id")]
    target_ids = set(_parse_action_ids(action_id, available_ids))

    found_ids = set()
    updated_actions = []

    for action in actions:
        aid = action.get("id", "").upper()
        if aid in target_ids:
            found_ids.add(aid)
            item = dict(action)
            item["status"] = target_status
            if target_status == "completed":
                item["completed_at"] = datetime.now(timezone.utc).isoformat()
            else:
                item["completed_at"] = None
            updated_actions.append(item)
        else:
            updated_actions.append(action)

    if not found_ids:
        raise ValueError(f"Action '{action_id}' not found in case actions.")

    # Check if all actions are completed/cancelled
    current_case_status = state.get("status", "action_required")
    if updated_actions and all(a.get("status") in ("completed", "cancelled") for a in updated_actions):
        current_case_status = "resolved"

    updated_str = ", ".join(sorted(found_ids))
    return Command(
        update={
            "actions": updated_actions,
            "status": current_case_status,
            "messages": [
                ToolMessage(
                    content=f"Updated action(s) {updated_str} to '{target_status}'. Current case status: {current_case_status}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool
def update_case_status(status: str, runtime: ToolRuntime) -> Command:
    """Update the overall operational case status.

    Args:
        status: The target status ('new', 'analyzed', 'action_required', 'in_progress', 'resolved', 'closed').
    """
    target = status.lower().strip()
    if target not in VALID_CASE_STATUSES:
        raise ValueError(
            f"Invalid case status '{status}'. Must be one of: {sorted(VALID_CASE_STATUSES)}"
        )

    state = runtime.state or {}
    current_status = state.get("status", "new")
    if current_status == "closed" and target not in {"closed", "in_progress"}:
        raise ValueError(
            "A closed case must be reopened to 'in_progress' before another transition."
        )

    return Command(
        update={
            "status": target,
            "messages": [
                ToolMessage(
                    content=f"Updated shipment case status to '{target}'.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
