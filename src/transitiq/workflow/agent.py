import json
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt

from transitiq.llm.openrouter_service import get_openrouter_client
from transitiq.workflow.middleware import load_ticket
from transitiq.workflow.state import TransitState
from transitiq.workflow.tools.actions import get_actions, update_action
from transitiq.workflow.tools.analysis import (
    analyze_case,
    get_analysis_history,
    reanalyze_case,
)
from transitiq.workflow.tools.case import get_case, update_case_status
from transitiq.workflow.tools.context import add_context
from transitiq.workflow.prompts.system import TRANSITIQ_SYSTEM_PROMPT


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
        "raw_text": state.get("raw_text"),
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
    llm = get_openrouter_client()
    return create_agent(
        model=llm,
        tools=OPERATIONAL_TOOLS,
        state_schema=TransitState,
        middleware=[load_ticket, case_prompt],
        checkpointer=checkpointer,
    )