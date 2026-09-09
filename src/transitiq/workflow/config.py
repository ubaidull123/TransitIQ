def shipment_thread_config(shipment_id: int) -> dict[str, dict[str, str]]:
    """Return the single checkpoint identity used for a shipment case."""
    return {"configurable": {"thread_id": f"shipment:{shipment_id}"}}
