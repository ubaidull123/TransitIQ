from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    """Validated input for a new shipment exception ticket."""

    model_config = ConfigDict(str_strip_whitespace=True)

    origin: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    carrier: str = Field(min_length=1, max_length=255)
    issue_description: str = Field(min_length=5)


class TicketResponse(TicketCreate):
    """Ticket returned after durable intake and thread initialization."""

    shipment_id: int
    created_at: datetime
