from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from transitiq.database.db import get_database_uri, initialize_ticket_schema
from transitiq.database.repositories import ticket_repository
from transitiq.models import TicketCreate, TicketResponse
from transitiq.services.ticket_service import TicketService
from transitiq.workflow.agent import create_transit_agent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own the shared checkpointer and agent for the application lifetime."""
    await initialize_ticket_schema()
    async with AsyncPostgresSaver.from_conn_string(get_database_uri()) as checkpointer:
        await checkpointer.setup()
        agent = create_transit_agent(checkpointer=checkpointer)
        app.state.ticket_service = TicketService(ticket_repository, agent)
        yield


def create_app(lifespan_context: Callable[..., Any] | None = lifespan) -> FastAPI:
    """Build the API, with a small dependency seam for deterministic tests."""
    application = FastAPI(title="TransitIQ", version="0.2.0", lifespan=lifespan_context)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post(
        "/exceptions",
        response_model=TicketResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_exception(payload: TicketCreate, request: Request) -> dict:
        return await request.app.state.ticket_service.create_ticket(payload)

    return application


app = create_app()
