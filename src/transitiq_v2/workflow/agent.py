from langchain.agents import create_agent
from transitiq_v2.llm.openrouter_service import get_openrouter_client
from transitiq_v2.workflow.middlewere import apply_transit_step
from transitiq_v2.workflow.state import TransitState

from transitiq_v2.workflow.Tools.classification_tool import classify_exception_type as record_exception_type
from transitiq_v2.workflow.Tools.severity_tool import record_severity as record_severity
from transitiq_v2.workflow.Tools.missing_info_tool import record_missing_info as record_missing_information
from transitiq_v2.workflow.Tools.recomendation_tool import provide_recommendations as record_recommendations
from transitiq_v2.workflow.middlewere import apply_transit_step

llm = get_openrouter_client()



agent = create_agent(
        model = llm,
    tools = [
        record_exception_type,
        record_severity,
        record_missing_information,
        record_recommendations,

    ],
    state_schema=TransitState,
    middleware=[
        apply_transit_step
    ]

) 
