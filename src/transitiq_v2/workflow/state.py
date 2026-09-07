from langchain.agents import AgentState
from typing import List, Literal, NotRequired



Transitstep = Literal[
    "classification",
    "severity",
    "missing_info",
    "recommendation",
    "done",
]

class TransitState(AgentState):
    current_step: NotRequired[Transitstep]
    issue_id: NotRequired[int]
    origin: NotRequired[str]
    destination: NotRequired[str]
    description: NotRequired[str]
    Issue_type: NotRequired[Literal[
        "Delayed shipment",
        "Missing documents",
        "Customs hold",
        "Incorrect address",
        "Damaged cargo",
        "Carrier cancellation",
        "Payment/document mismatch",
        "Insufficient information",
    ]]
    severity: Literal["Low", "Medium", "High", "Critical"]
    missing_info: str
    actions: List[str]