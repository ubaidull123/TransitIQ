from typing import Any

from langchain.agents.middleware import before_model
from sqlalchemy import select

from transitiq.database.db import AsyncSessionLocal
from transitiq.database.models import ShipmentException

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
    On subsequent executions for the same thread, the checkpointer restores state and this DB query is skipped.
    """
    if state.get("raw_text"):
        validate_ticket_description(state.get("raw_text"))
        return None

    shipment_id = state.get("shipment_id")
    if not shipment_id:
        raise ValueError("Missing shipment_id in state; cannot load shipment ticket.")

    async with AsyncSessionLocal() as session:
        record = await session.scalar(
            select(ShipmentException).where(ShipmentException.shipment_id == shipment_id)
        )
    if record is None:
        raise ValueError(f"Shipment {shipment_id} not found in shipment_exceptions table.")

    validate_ticket_description(record.raw_text)

    return {
        "shipment_id": record.shipment_id,
        "origin": record.origin,
        "destination": record.destination,
        "carrier": record.carrier,
        "raw_text": record.raw_text,
        "status": state.get("status") or "new",
        "current_step": state.get("current_step") or "new",
    }