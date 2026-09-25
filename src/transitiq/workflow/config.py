def shipment_thread_config(shipment_id: str) -> dict[str, dict[str, str]]:
    """Return the single checkpoint identity used for a shipment exception thread."""
    return {"configurable": {"thread_id": f"shipment:{shipment_id}"}}