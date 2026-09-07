from langchain.tools import tool ,ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Literal, List


@tool
def record_missing_info(missing_info: str, actions: List[str], runtime: ToolRuntime) -> Command:
    """
    Records the missing information and preferred actions provided by the agent.
    
    Args:
        missing_info (str): The missing information that caused the issue.
        actions (List[str]): Preferred actions provided by the agent.
        
    Returns:
        Command: A command object containing the recorded missing information and actions.
    """
    return Command(
        update={
            "missing_info": missing_info,
            "actions": actions,
            "current_step": "recommendation",
            "messages":[
                ToolMessage(
                    content=f"Recorded missing information: {missing_info} and preferred actions: {actions}. Proceeding to recommendation.",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )