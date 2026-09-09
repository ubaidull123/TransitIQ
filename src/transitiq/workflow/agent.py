import json
from typing import Any
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from transitiq.llm.openrouter_service import get_openrouter_client
from transitiq.workflow.middleware import load_ticket
from transitiq.workflow.state import TransitState
from transitiq.workflow.Tools.operational_tools import (
    add_context,
    analyze_case,
    get_actions,
    get_analysis_history,
    get_case,
    reanalyze_case,
    update_action,
    update_case_status,
)

TRANSITIQ_SYSTEM_PROMPT = """You are TransitIQ, an autonomous logistics exception management agent.
Your mission is to analyze shipment exceptions, evaluate severity, identify missing information, propose and manage operational actions, and track chronological case context.

Operational Tools Available:
- analyze_case: Perform the initial exception analysis and create the initial action items.
- reanalyze_case: Re-evaluate the shipment when new facts or context are provided.
- add_context: Record operational updates, notes, or external messages with their source and content.
- get_case: Retrieve complete current state of the shipment case.
- get_actions: View all operational actions and their current status (pending, in_progress, completed, cancelled).
- update_action: Update an action item's status (e.g., mark as completed).
- update_case_status: Set the overall case status (new, analyzed, action_required, in_progress, resolved, closed).
- get_analysis_history: View all historical analysis runs for this case.

Always execute the appropriate tool when the user asks you to analyze, add context, update actions, or manage status.
Call at most one state-changing tool in a response.
Never invent shipment facts not present in the ticket, context, or analysis history.
"""

OPERATIONAL_TOOLS = [
    analyze_case,
    reanalyze_case,
    add_context,
    get_case,
    get_analysis_history,
    get_actions,
    update_action,
    update_case_status,
]


@dynamic_prompt
def case_prompt(request: ModelRequest) -> str:
    """Give the model the current persisted case without duplicating it in user input."""
    state = request.state
    case = {
        "shipment_id": state.get("shipment_id"),
        "origin": state.get("origin"),
        "destination": state.get("destination"),
        "carrier": state.get("carrier"),
        "issue_description": state.get("issue_description"),
        "status": state.get("status", "new"),
        "exception_type": state.get("exception_type"),
        "severity": state.get("severity"),
        "missing_information": state.get("missing_information", []),
        "recommended_actions": state.get("recommended_actions", []),
        "context": state.get("context", []),
        "actions": state.get("actions", []),
        "latest_analysis": state.get("latest_analysis"),
    }
    return (
        f"{TRANSITIQ_SYSTEM_PROMPT}\n\n"
        "Current persisted shipment case:\n"
        f"{json.dumps(case, default=str)}"
    )


def create_transit_agent(checkpointer: Any = None, model: Any = None):
    """Factory to create a compiled TransitIQ agent with optional checkpointer and model."""
    llm = model or get_openrouter_client()
    return create_agent(
        model=llm,
        tools=OPERATIONAL_TOOLS,
        state_schema=TransitState,
        middleware=[load_ticket, case_prompt],
        checkpointer=checkpointer,
    )
