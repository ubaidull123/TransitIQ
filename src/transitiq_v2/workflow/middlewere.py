from langchain.agents.middleware import (
    wrap_model_call,
    ModelRequest,
    ModelResponse,
)
from typing import Callable

from langchain.messages import SystemMessage

from transitiq_v2.workflow.Tools.tool_config import STEP_CONFIG


@wrap_model_call
def apply_transit_step(
    request : ModelRequest, 
    handler: Callable[[ModelRequest], ModelResponse]
)-> ModelResponse:
    """
    Middleware to apply the current transit step to the model request.
    
    Args:
        request (ModelRequest): The incoming model request.
        handler (Callable): The next handler in the middleware chain.
        
    Returns:
        ModelResponse: The response from the model after applying the transit step.
    """
    current_step = request.state.get("current_step", "classification")

    config = STEP_CONFIG[current_step]

    request = request.override(
        system_message=SystemMessage(content=config["prompt"]),
        tools=config["tools"],
    )

    return handler(request)