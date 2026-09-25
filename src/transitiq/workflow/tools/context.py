from datetime import datetime, timezone

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


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