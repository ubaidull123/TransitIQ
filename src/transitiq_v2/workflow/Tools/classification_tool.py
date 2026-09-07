from langchain.tools import tool ,ToolRuntime
from langchain.messages import ToolMessage
from langchain_protocol import UpdatesEvent
from langgraph.types import Command
from typing import Literal
from transitiq_v2.workflow.state import TransitState


@tool
def classify_exception_type(exception_type: Literal[
    "Delayed shipment",
    "Missing documents",
    "Customs hold",
    "Incorrect address",
    "Damaged cargo",
    "Carrier cancellation",
    "Payment/document mismatch",
],
    runtime: ToolRuntime
) -> Command:
    """
    Classifies the type of exception based on the provided exception type.
    
    Args:
        exception_type (Literal): The type of exception encountered during shipment.
        
    Returns:
        ToolRuntime: A runtime object containing the classified exception type.
    """
    return Command(
        update={
            exception_type: exception_type,
            "current_step": "severity",
            "messages":[
                ToolMessage(
                    content=f"Classified exception type: {exception_type}. Proceeding to severity classification.",
                    tool_call_id=runtime.tool_call_id,
                )
            ]

        }
    )
  