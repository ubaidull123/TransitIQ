from langchain.tools import tool , ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import List


@tool
def provide_recommendations(recommendations: List[str], runtime: ToolRuntime) -> Command:
    """
    Provides recommendations based on the recorded missing information and preferred actions.
    
    Args:
        recommendations (List[str]): A list of recommendations for resolving the issue.
        runtime (ToolRuntime): The runtime context for the tool.
        
    Returns:
        Command: A command object containing the provided recommendations.
    """
    return Command(
        update={
            "recommendations": recommendations,
            "current_step": "done",
            "messages": [
                ToolMessage(
                    content=f"Provided recommendations: {recommendations}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )