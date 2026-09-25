import asyncio
import logging
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from transitiq.api.routers.exception_routes import exception_handlers, router
from transitiq.database.db import Base, engine, get_db
from transitiq.database.models.exception_model import ShipmentException

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    async def _create() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(_create())


@pytest.fixture
async def session():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint"
        )
        try:
            await async_session.execute(delete(ShipmentException))
            yield async_session
        finally:
            await async_session.close()
            await transaction.rollback()


class FakeSnapshot:
    def __init__(self, values: dict[str, Any], created_at: Any = None) -> None:
        self.values = values
        self.created_at = created_at


class FakeAgent:
    """Stands in for the compiled LangGraph agent so routes can be tested without an LLM.

    Records what it was asked to do so tests can assert on the resulting state
    rather than on mock call counts.
    """

    def __init__(self) -> None:
        self.seeded: list[tuple[dict[str, Any], dict[str, Any]]] = []
        self.invoked_thread_ids: list[str] = []
        self.invoke_inputs: list[Any] = []
        self.invoke_attempts = 0
        self.fail_on_invoke = False
        self.result_text: str | None = None
        self.state_values: dict[str, Any] = {}
        self.state_created_at: Any = None
        self.state_reads: list[str] = []
        self.result_state: dict[str, Any] | None = None

    async def aget_state(self, config: dict[str, Any], **kwargs: Any) -> FakeSnapshot:
        self.state_reads.append(config["configurable"]["thread_id"])
        return FakeSnapshot(self.state_values, self.state_created_at)

    async def aupdate_state(self, config: dict[str, Any], state: dict[str, Any]) -> None:
        self.seeded.append((config, state))
        self.state_values = {**self.state_values, **state}

    async def ainvoke(self, payload: Any, config: dict[str, Any] | None = None) -> Any:
        self.invoke_attempts += 1
        if self.fail_on_invoke:
            raise RuntimeError("model unavailable")
        if config is not None:
            self.invoked_thread_ids.append(config["configurable"]["thread_id"])
        self.invoke_inputs.append(payload)
        if self.result_state:
            self.state_values = {**self.state_values, **self.result_state}
        if self.result_text is None:
            return {"messages": []}
        return {"messages": [SimpleNamespace(content=self.result_text)]}


@pytest.fixture
def agent() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
async def client(session: AsyncSession, agent: FakeAgent):
    app = FastAPI(exception_handlers=exception_handlers)
    app.include_router(router)
    app.state.agent = agent

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        yield http_client


@pytest.fixture
def make_exception():
    def _make(**overrides: Any) -> ShipmentException:
        fields: dict[str, Any] = {
            "shipment_id": "SHP-1",
            "source": "manual",
            "reported_at": datetime(2026, 1, 1, tzinfo=UTC),
            "carrier": "Maersk",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "raw_text": "Container held at customs",
            "meta_data": None,
        }
        fields.update(overrides)
        return ShipmentException(**fields)

    return _make