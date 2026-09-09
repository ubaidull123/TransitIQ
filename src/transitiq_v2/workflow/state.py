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
    carrier: NotRequired[str]
    description: NotRequired[str]
    exception_type: NotRequired[Literal[
        "Delayed shipment",
        "Missing documents",
        "Customs hold",
        "Incorrect address",
        "Damaged cargo",
        "Carrier cancellation",
        "Payment/document mismatch",
        "Insufficient information",
    ]]
    severity: NotRequired[Literal["Low", "Medium", "High", "Critical"]]
    missing_info: NotRequired[str]
    actions: NotRequired[List[str]]
    recommendations: NotRequired[List[str]]
