import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from transitiq.api.schemas.exception_schema import Exception as ExceptionPayload
from transitiq.database.models.exception_model import ShipmentException
from transitiq.workflow.config import analysis_request, shipment_thread_config
from transitiq.workflow.state import create_initial_state

logger = logging.getLogger(__name__)


class DuplicateShipmentError(Exception):
    def __init__(self, shipment_id: str) -> None:
        super().__init__(f"shipment_id {shipment_id!r} already has a recorded exception")
        self.shipment_id = shipment_id


async def save_exception(
    payload: ExceptionPayload, session: AsyncSession
) -> ShipmentException:
    record = ShipmentException(
        shipment_id=payload.shipment_id,
        source=payload.source,
        reported_at=payload.reported_at,
        carrier=payload.carrier,
        origin=payload.origin,
        destination=payload.destination,
        raw_text=payload.raw_text,
        meta_data=payload.metadata,
    )
    session.add(record)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise DuplicateShipmentError(payload.shipment_id) from None
    await session.refresh(record)
    return record


async def start_exception_analysis(agent: Any, shipment_id: str) -> None:
    thread = shipment_thread_config(shipment_id)
    await agent.aupdate_state(thread, create_initial_state(shipment_id))
    try:
        await agent.ainvoke(analysis_request(shipment_id), thread)
    except Exception as exc:
        logger.exception("agent_analysis_failed shipment_id=%s", shipment_id)
        await agent.aupdate_state(
            thread, {"analysis_error": str(exc) or type(exc).__name__}
        )


async def load_exception(
    session: AsyncSession, shipment_id: str
) -> ShipmentException | None:
    return await session.scalar(
        select(ShipmentException).where(ShipmentException.shipment_id == shipment_id)
    )


async def read_exception_analysis(agent: Any, shipment_id: str) -> dict[str, Any]:
    snapshot = await agent.aget_state(shipment_thread_config(shipment_id))
    values = dict(snapshot.values or {})
    return {
        "shipment_id": shipment_id,
        "status": values.get("status") or "new",
        "current_step": values.get("current_step") or "new",
        "analysis_error": values.get("analysis_error"),
        "exception_type": values.get("exception_type"),
        "severity": values.get("severity"),
        "missing_information": list(values.get("missing_information") or []),
        "recommended_actions": list(values.get("recommended_actions") or []),
        "actions": list(values.get("actions") or []),
        "context": list(values.get("context") or []),
        "analysis_history": list(values.get("analysis_history") or []),
        "updated_at": snapshot.created_at,
    }