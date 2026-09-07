from langchain.tools import tool ,ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Literal




@tool
def record_severity(severity: Literal["Low", "Medium", "High", "Critical"],
    runtime: ToolRuntime
) -> Command:
    """
    Records the severity level of the issue based on the provided severity.
    
    Args:
        severity (Literal): The severity level of the issue.
        
    Returns:
        Command: A command object containing the recorded severity level.
    """
    return Command(
        update={
            "severity": severity,
            "current_step": "missing_info",
            "messages":[
                ToolMessage(
                    content=f"Recorded severity level: {severity}. Proceeding to missing information collection.",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )