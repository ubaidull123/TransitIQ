from transitiq_v2.workflow.Tools.classification_tool import classify_exception_type as record_exception_type
from transitiq_v2.workflow.Tools.severity_tool import record_severity as record_severity
from transitiq_v2.workflow.Tools.missing_info_tool import record_missing_info as record_missing_information
from transitiq_v2.workflow.Tools.recomendation_tool import provide_recommendations as record_recommendations

STEP_CONFIG = {

    "classification": {
        "prompt": """
You are TransitIQ, a logistics exception analysis agent.

Analyze the shipment problem and determine its primary
exception category.

You MUST call record_exception_type when you have decided.
""",
        "tools": [record_exception_type],
    },

    "severity": {
        "prompt": """
You are evaluating the operational severity of a shipment exception.

Consider:
- delay impact
- customs impact
- cargo risk
- customer impact
- urgency

Classify severity as low, medium, or high.

You MUST call record_severity.
""",
        "tools": [record_severity],
    },

    "missing_info": {
        "prompt": """
Determine what important information is missing before
operations can properly resolve this shipment exception.

Call record_missing_information.
Use an empty list if nothing important is missing.
""",
        "tools": [record_missing_information],
    },

    "recommendation": {
        "prompt": """
Based on the shipment exception, severity, and available
information, determine the most useful next operational actions.

Call record_recommendations.
""",
        "tools": [record_recommendations],
    },

    "done": {
        "prompt": """
The shipment exception analysis is complete.

Return the final summary in English only.
Do not invent shipment facts.
If the supplied data is meaningless or insufficient, clearly state that the shipment cannot be analyzed.
""",
        "tools": [],
    },
}