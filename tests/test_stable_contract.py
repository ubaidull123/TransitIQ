from datetime import datetime, timezone
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from transitiq.api.app import create_app
from transitiq.models import TicketCreate
from transitiq.services.ticket_service import TicketService
from transitiq.workflow.Tools.operational_tools import reanalyze_case
from transitiq.workflow.state import reduce_status


class FakeRepository:
    async def create(self, data: dict) -> dict:
        return {
            "shipment_id": 42,
            **data,
            "created_at": datetime.now(timezone.utc),
        }


class FakeAgent:
    def __init__(self) -> None:
        self.update = None

    async def aupdate_state(self, config: dict, state: dict) -> None:
        self.update = (config, state)


async def test_ticket_service_saves_ticket_and_initializes_thread():
    agent = FakeAgent()
    service = TicketService(FakeRepository(), agent)

    ticket = await service.create_ticket(
        TicketCreate(
            origin="Karachi",
            destination="Dubai",
            carrier="Test Carrier",
            issue_description="Customs documentation mismatch",
        )
    )

    assert ticket["shipment_id"] == 42
    assert agent.update[0]["configurable"]["thread_id"] == "shipment:42"
    assert agent.update[1]["shipment_id"] == 42
    assert agent.update[1]["issue_description"] == ""


async def test_post_exceptions_uses_ticket_service():
    app = create_app(lifespan_context=None)
    app.state.ticket_service = TicketService(FakeRepository(), FakeAgent())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/exceptions",
            json={
                "origin": "Karachi",
                "destination": "Dubai",
                "carrier": "Test Carrier",
                "issue_description": "Customs documentation mismatch",
            },
        )

    assert response.status_code == 201
    assert response.json()["shipment_id"] == 42


def test_reanalysis_preserves_existing_actions():
    existing_action = {"id": "ACT-1", "description": "Call broker", "status": "pending"}
    runtime = SimpleNamespace(
        state={
            "shipment_id": 42,
            "actions": [existing_action],
            "analysis_history": [{"exception_type": "delay", "created_at": "earlier"}],
        },
        tool_call_id="test-call",
    )

    command = reanalyze_case.func(
        exception_type="customs_hold",
        severity="high",
        missing_information=[],
        recommended_actions=["Call broker"],
        runtime=runtime,
    )

    assert command.update["actions"] == [existing_action]
    assert len(command.update["analysis_history"]) == 2


def test_latest_status_can_reopen_closed_case():
    assert reduce_status("closed", "in_progress") == "in_progress"
