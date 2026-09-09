from pydantic import BaseModel , Field
from typing import Optional ,List
from datetime import datetime

class UserInputs(BaseModel):
    """
    cargo/shipment details provided by user to the system for processing and analysis.
    """
    shipment_id : Optional[int] = Field(None, description="Unique identifier for the cargo/shipment")
    origin : str = Field(..., description="Origin location of the cargo/shipment")
    destination : str = Field(..., description="cargo/shipment destination location")
    carrier : str = Field(..., description="Carrier details")
    issue_description : str = Field(..., description="issue provided by user about shipment")

class AgentOutput(BaseModel):
        exception_type: str = Field(..., description="Problem classification")
        severity: str = Field(..., description="Priorty level of Exception")
        missing_info: str = Field(..., description="the missing info that caused exception")
        actions: List[str] = Field(..., description="prefered actions provided by the agent")


class AnalysisResponse(BaseModel):
    id: int
    exception_id: int
    exception_type: str
    severity: str
    missing_information: str
    recommended_actions: List[str]
    model_name: str
    created_at: datetime
