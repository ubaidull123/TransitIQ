from typing import Any
from langchain.agents.middleware import before_model

from transitiq.database.repositories import ticket_repository

INSUFFICIENT_DESCRIPTIONS = {"bad", "n/a", "none", "null", "error", "unknown", "test"}


def validate_ticket_description(description: str | None) -> None:
    """Validate that the ticket description is substantive enough for operational analysis."""
    if not description:
        raise ValueError("Ticket description is empty or missing.")
    cleaned = description.strip().lower()
    if len(cleaned) < 5 or cleaned in INSUFFICIENT_DESCRIPTIONS:
        raise ValueError(
            f"Invalid or insufficient ticket description: '{description}'. "
            "Cannot perform operational analysis."
        )


@before_model
async def load_ticket(state: dict[str, Any], runtime: Any) -> dict[str, Any] | None:
    """Middleware to hydrate shipment ticket information from PostgreSQL into agent state on first execution.

    On subsequent executions for the same thread, PostgresSaver restores state and this DB query is skipped.
    """
    if state.get("issue_description"):
        validate_ticket_description(state.get("issue_description"))
        return None

    shipment_id = state.get("shipment_id")
    if not shipment_id:
        raise ValueError("Missing shipment_id in state; cannot load shipment ticket.")

    ticket = await ticket_repository.get(shipment_id)
    if not ticket:
        raise ValueError(f"Shipment {shipment_id} not found in issues database.")

    validate_ticket_description(ticket.get("issue_description"))

    return {
        "shipment_id": ticket["shipment_id"],
        "origin": ticket["origin"],
        "destination": ticket["destination"],
        "carrier": ticket["carrier"],
        "issue_description": ticket["issue_description"],
        "status": state.get("status") or "new",
        "current_step": state.get("current_step") or "new",
    }

