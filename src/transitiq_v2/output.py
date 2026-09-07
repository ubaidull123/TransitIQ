from pydantic import BaseModel , Field
from typing import List 

class Output(BaseModel):
    exception_type : str = Field(..., description="Problem classification")
    severity : str = Field(..., description="Priorty level of Exception")
    missing_info : str = Field(..., description="the missing info that caused exception")
    actions : List[str] = Field(..., description="prefered actions provided by the agent")
