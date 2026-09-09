from typing import Any

from transitiq.models import TicketCreate
from transitiq.workflow.config import shipment_thread_config
from transitiq.workflow.state import create_initial_state


class TicketService:
    """Create immutable tickets and initialize their agent checkpoint."""

    def __init__(self, repository: Any, agent: Any) -> None:
        self.repository = repository
        self.agent = agent

    async def create_ticket(self, ticket_input: TicketCreate) -> dict:
        ticket = await self.repository.create(ticket_input.model_dump())
        shipment_id = ticket["shipment_id"]
        await self.agent.aupdate_state(
            shipment_thread_config(shipment_id),
            create_initial_state(shipment_id),
        )
        return ticket
