from typing import Any

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


@tool
def get_case(runtime: ToolRuntime) -> dict[str, Any]:
    """Retrieve the current full shipment case state directly from active state."""
    state = runtime.state or {}
    return {
        "shipment_id": state.get("shipment_id"),
        "origin": state.get("origin"),
        "destination": state.get("destination"),
        "carrier": state.get("carrier"),
        "raw_text": state.get("raw_text"),
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
def update_case_status(status: str, runtime: ToolRuntime) -> Command:
    """Update the overall operational case status.

    Args:
        status: The target status ('new', 'analyzed', 'action_required', 'in_progress', 'resolved', 'closed').
    """
    target = status.lower().strip()
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