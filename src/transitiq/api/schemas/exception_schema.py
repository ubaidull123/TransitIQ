from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


ExceptionSource = Literal["email", "edi", "webhook", "manual"]


class Exception(BaseModel):
    shipment_id: str
    source: ExceptionSource
    reported_at: datetime
    carrier: str
    origin: str
    destination: str
    raw_text: str = Field(..., min_length=1)
    metadata: Optional[dict] = None


class ExceptionResponse(Exception):
    id: int


class ErrorDetail(BaseModel):

    field: str
    message: str


class ErrorBody(BaseModel):

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody