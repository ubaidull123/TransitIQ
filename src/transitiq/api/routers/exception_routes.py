import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from transitiq.api.schemas.exception_schema import (
    AnalysisResponse,
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    Exception as ExceptionPayload,
    ExceptionResponse,
    ExceptionSource,
)
from transitiq.database.db import get_db
from transitiq.database.models.exception_model import ShipmentException
from transitiq.api.status_codes import STATUS_CODES
from transitiq.services.exception_service import (
    DuplicateShipmentError,
    load_exception,
    read_exception_analysis,
    save_exception,
    start_exception_analysis,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_agent(request: Request) -> Any:
    return request.app.state.agent

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/exceptions",response_model=ExceptionResponse, status_code=status.HTTP_201_CREATED)
async def create_exception(
    payload: ExceptionPayload,
    session: AsyncSession = Depends(get_db),
    agent: Any = Depends(get_agent),
) -> ExceptionResponse:
    try:
        record = await save_exception(payload, session)
    except DuplicateShipmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    await start_exception_analysis(agent, record.shipment_id)

    return _to_response(record)


@router.get("/exceptions", response_model=list[ExceptionResponse])
async def list_exceptions(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
) -> list[ExceptionResponse]:
    result = await session.execute(
        select(ShipmentException)
        .order_by(ShipmentException.reported_at.desc(), ShipmentException.id.desc())
        .limit(limit)
    )
    return [_to_response(record) for record in result.scalars().all()]


@router.get("/exceptions/{shipment_id}/analysis", response_model=AnalysisResponse)
async def get_exception_analysis(
    shipment_id: str,
    session: AsyncSession = Depends(get_db),
    agent: Any = Depends(get_agent),
) -> AnalysisResponse:
    await _require_exception(session, shipment_id)
    return AnalysisResponse.model_validate(
        await read_exception_analysis(agent, shipment_id)
    )


@router.post("/exceptions/{shipment_id}/analyze", response_model=AnalysisResponse)
async def analyze_exception(
    shipment_id: str,
    session: AsyncSession = Depends(get_db),
    agent: Any = Depends(get_agent),
) -> AnalysisResponse:
    await _require_exception(session, shipment_id)
    await start_exception_analysis(agent, shipment_id)
    return AnalysisResponse.model_validate(
        await read_exception_analysis(agent, shipment_id)
    )


async def _require_exception(
    session: AsyncSession, shipment_id: str
) -> ShipmentException:
    record = await load_exception(session, shipment_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"shipment_id {shipment_id!r} has no recorded exception",
        )
    return record


def _to_response(record: ShipmentException) -> ExceptionResponse:

    return ExceptionResponse(
        id=record.id,
        shipment_id=record.shipment_id,
        source=cast(ExceptionSource, record.source),
        reported_at=record.reported_at,
        carrier=record.carrier,
        origin=record.origin,
        destination=record.destination,
        raw_text=record.raw_text,
        metadata=record.meta_data,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse: 
    
    logger.warning(
        "http_error status=%s method=%s path=%s",
        exc.status_code,
        request.method,
        request.url.path,
    )
    if exc.status_code >= 500:
        message = "Internal server error"
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorBody(
                code=STATUS_CODES.get(exc.status_code, "http_error"),
                message=message,
            )
        ).model_dump(),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
        )
        for error in exc.errors()
    ]
    logger.warning(
        "validation_error method=%s path=%s fields=%s",
        request.method,
        request.url.path,
        [detail.field for detail in details],
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            error=ErrorBody(
                code="validation_error",
                message="Request failed validation",
                details=details,
            )
        ).model_dump(),
    )


exception_handlers = {
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
}

