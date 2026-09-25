from typing import Annotated, Any

from langchain.agents import AgentState


def reduce_last(current: Any, new: Any) -> Any:
    return new if new is not None else current


def reduce_status(current: str | None, new: str | None) -> str:
    return new if new is not None else (current or "new")


def reduce_actions(
    current: list[dict[str, Any]] | None, new: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    if not current:
        return list(new or [])
    if not new:
        return list(current)
    merged = {a.get("id"): dict(a) for a in current if a.get("id")}
    for a in new:
        aid = a.get("id")
        if aid:
            if aid in merged:
                merged[aid].update(a)
            else:
                merged[aid] = dict(a)
    return list(merged.values())


def reduce_context(
    current: list[dict[str, Any]] | None, new: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    if not current:
        return list(new or [])
    if not new:
        return list(current)
    seen = set()
    result = []
    for item in (*current, *new):
        key = (item.get("source"), item.get("content"), item.get("created_at"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def reduce_history(
    current: list[dict[str, Any]] | None, new: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    if not current:
        return list(new or [])
    if not new:
        return list(current)
    seen = set()
    result = []
    for item in (*current, *new):
        key = (item.get("exception_type"), item.get("created_at"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


class TransitState(AgentState, total=False):
    shipment_id: Annotated[str, reduce_last]
    origin: Annotated[str, reduce_last]
    destination: Annotated[str, reduce_last]
    carrier: Annotated[str, reduce_last]
    raw_text: Annotated[str, reduce_last]

    status: Annotated[str, reduce_status]
    current_step: Annotated[str, reduce_last]
    analysis_error: Annotated[str | None, reduce_last]

    exception_type: Annotated[str | None, reduce_last]
    severity: Annotated[str | None, reduce_last]

    missing_information: Annotated[list[str], reduce_last]
    recommended_actions: Annotated[list[str], reduce_last]

    latest_analysis: Annotated[dict[str, Any] | None, reduce_last]
    analysis_history: Annotated[list[dict[str, Any]], reduce_history]

    actions: Annotated[list[dict[str, Any]], reduce_actions]
    context: Annotated[list[dict[str, Any]], reduce_context]


def create_initial_state(
    shipment_id: str,
    origin: str = "",
    destination: str = "",
    carrier: str = "",
    raw_text: str = "",
    status: str = "new",
    current_step: str = "new",
) -> TransitState:
    return {
        "shipment_id": shipment_id,
        "origin": origin,
        "destination": destination,
        "carrier": carrier,
        "raw_text": raw_text,
        "status": status,
        "current_step": current_step,
        "analysis_error": None,
        "exception_type": None,
        "severity": None,
        "missing_information": [],
        "recommended_actions": [],
        "latest_analysis": None,
        "analysis_history": [],
        "actions": [],
        "context": [],
        "messages": [],
    }