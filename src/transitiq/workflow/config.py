from langchain.messages import HumanMessage


ANALYSIS_REQUEST = (
    "Analyze this shipment exception and record your findings using the available tools."
)


def shipment_thread_config(shipment_id: str) -> dict[str, dict[str, str]]:
    """Return the single checkpoint identity used for a shipment exception thread."""
    return {"configurable": {"thread_id": f"shipment:{shipment_id}"}}


def analysis_request(shipment_id: str) -> dict[str, object]:
    return {
        "shipment_id": shipment_id,
        "messages": [HumanMessage(content=f"{ANALYSIS_REQUEST} Shipment {shipment_id}.")],
    }