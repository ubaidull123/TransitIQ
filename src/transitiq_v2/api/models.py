from pydantic import BaseModel , Field
from typing import Optional

class UserInputs(BaseModel):
    """
    cargo/shipment details provided by user to the system for processing and analysis.
    """
    shipment_id : Optional[int] = Field(None, description="Unique identifier for the cargo/shipment")
    origin : str = Field(..., description="Origin location of the cargo/shipment")
    destination : str = Field(..., description="cargo/shipment destination location")
    carrier : str = Field(..., description="Carrier details")
    issue_description : str = Field(..., description="issue provided by user about shipment")