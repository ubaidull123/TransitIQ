from datetime import datetime, timezone
from typing import Any

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


@tool
def get_actions(runtime: ToolRuntime) -> list[dict[str, Any]]:
    """Retrieve all operational actions associated with this shipment case directly from active state."""
    state = runtime.state or {}
    return list(state.get("actions") or [])


@tool
def update_action(action_id: list[str], status: str, runtime: ToolRuntime) -> Command:
    """Update the status of one or multiple action items.

    Args:
        action_id: The IDs of the actions to update (e.g. ['ACT-1', 'ACT-2']).
        status: The new status ('pending', 'in_progress', 'completed', 'cancelled').
    """
    target_status = status.lower().strip()
    state = runtime.state or {}
    actions = list(state.get("actions") or [])
    target_ids = set(action_id)

    found_ids: set[str] = set()
    updated_actions = []

    for action in actions:
        if action.get("id") in target_ids:
            found_ids.add(action["id"])
            item = dict(action)
            item["status"] = target_status
            item["completed_at"] = (
                datetime.now(timezone.utc).isoformat()
                if target_status == "completed"
                else None
            )
            updated_actions.append(item)
        else:
            updated_actions.append(action)

    current_case_status = state.get("status", "action_required")
    if updated_actions and all(
        a.get("status") in ("completed", "cancelled") for a in updated_actions
    ):
        current_case_status = "resolved"

    if found_ids:
        content = (
            f"Updated action(s) {', '.join(sorted(found_ids))} to '{target_status}'. "
            f"Current case status: {current_case_status}."
        )
    else:
        content = f"No action matched {action_id}. Nothing changed."

    return Command(
        update={
            "actions": updated_actions,
            "status": current_case_status,
            "messages": [ToolMessage(content=content, tool_call_id=runtime.tool_call_id)],
        }
    )