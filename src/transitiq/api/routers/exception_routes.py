import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from transitiq.api.schemas.exception_schema import (
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    Exception,
    ExceptionResponse,
    ExceptionSource,
)
from transitiq.database.db import get_db
from transitiq.database.models import ShipmentException
from transitiq.workflow.config import shipment_thread_config
from transitiq.workflow.state import create_initial_state

logger = logging.getLogger(__name__)

router = APIRouter()

_STATUS_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "unprocessable_entity",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_server_error",
}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/exceptions",response_model=ExceptionResponse, status_code=status.HTTP_201_CREATED)
async def create_exception(
    payload: Exception,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> ExceptionResponse:
    """Store a reported shipment exception."""
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"shipment_id {payload.shipment_id!r} already has a recorded exception",
        ) from None
    await session.refresh(record)
    await request.app.state.agent.aupdate_state(
        shipment_thread_config(record.shipment_id),
        create_initial_state(record.shipment_id),
    )
    return _to_response(record)


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
                code=_STATUS_CODES.get(exc.status_code, "http_error"),
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
                message="Request body failed validation",
                details=details,
            )
        ).model_dump(),
    )


exception_handlers = {
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
}

