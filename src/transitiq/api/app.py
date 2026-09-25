from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from transitiq.api.routers.exception_routes import exception_handlers, router
from transitiq.database import models  
from transitiq.database.db import Base, engine, get_database_uri
from transitiq.workflow.agent import create_transit_agent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create missing tables on startup, release the connection pool on shutdown."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncPostgresSaver.from_conn_string(get_database_uri()) as checkpointer:
        await checkpointer.setup()
        app.state.agent = create_transit_agent(checkpointer=checkpointer)
        yield
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="TransitIQ",
        version="0.2.0",
        lifespan=lifespan,
        exception_handlers=exception_handlers,
    ) 
    application.include_router(router)
    return application


app = create_app()