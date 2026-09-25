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


class AnalysisResponse(BaseModel):
    shipment_id: str
    status: str
    current_step: str
    analysis_error: Optional[str] = None
    exception_type: Optional[str] = None
    severity: Optional[str] = None
    missing_information: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    context: list[dict] = Field(default_factory=list)
    analysis_history: list[dict] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    error: ErrorBody