import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select

from transitiq.database.db import Base, AsyncSessionLocal, engine, get_database_uri
from transitiq.database.models.exception_model import ShipmentException
from transitiq.workflow.agent import create_transit_agent
from transitiq.workflow.config import analysis_request, shipment_thread_config


class TransitArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args: Any = None, namespace: Any = None) -> argparse.Namespace:
        parsed = super().parse_args(args, namespace)
        if not parsed.shipment_id and not parsed.dataset:
            self.error("one of shipment_id or --dataset is required")
        if parsed.shipment_id and parsed.dataset:
            self.error("shipment_id and --dataset cannot be used together")
        return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = TransitArgumentParser(
        prog="transitiq",
        description="Run the analysis agent against one or more shipment exceptions.",
    )
    parser.add_argument(
        "shipment_id",
        nargs="?",
        help="shipment_id of a stored exception, for example SHP-1",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        help="seed valid_cases from a JSON dataset and analyze each shipment",
    )
    return parser


async def analyze_shipment(agent: Any, shipment_id: str) -> str:
    result = await agent.ainvoke(
        analysis_request(shipment_id), shipment_thread_config(shipment_id)
    )
    messages = result.get("messages") or []
    if not messages:
        return ""
    return messages[-1].content or ""


async def run(shipment_id: str) -> str:
    async with AsyncPostgresSaver.from_conn_string(get_database_uri()) as checkpointer:
        await checkpointer.setup()
        agent = create_transit_agent(checkpointer=checkpointer)
        return await analyze_shipment(agent, shipment_id)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as dataset_file:
        dataset = json.load(dataset_file)
    cases = dataset.get("valid_cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset must contain a non-empty valid_cases list")
    return cases


async def seed_dataset(cases: list[dict[str, Any]]) -> list[str]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    seeded_ids: list[str] = []
    async with AsyncSessionLocal() as session:
        for case in cases:
            payload = case["input"]
            shipment_id = payload["shipment_id"]
            existing = await session.scalar(
                select(ShipmentException).where(
                    ShipmentException.shipment_id == shipment_id
                )
            )
            if existing is not None:
                continue
            session.add(
                ShipmentException(
                    shipment_id=shipment_id,
                    source=payload["source"],
                    reported_at=datetime.fromisoformat(payload["reported_at"].replace("Z", "+00:00")),
                    carrier=payload["carrier"],
                    origin=payload["origin"],
                    destination=payload["destination"],
                    raw_text=payload["raw_text"],
                    meta_data=payload.get("metadata"),
                )
            )
            seeded_ids.append(shipment_id)
        await session.commit()
    return seeded_ids


async def run_dataset(path: Path) -> None:
    cases = load_dataset(path)
    await seed_dataset(cases)
    async with AsyncPostgresSaver.from_conn_string(get_database_uri()) as checkpointer:
        await checkpointer.setup()
        agent = create_transit_agent(checkpointer=checkpointer)
        for case in cases:
            shipment_id = case["input"]["shipment_id"]
            text = await analyze_shipment(agent, shipment_id)
            print(f"[{shipment_id}] {text or 'No analysis produced.'}")


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    args = build_parser().parse_args()
    if args.dataset:
        asyncio.run(run_dataset(args.dataset))
        return
    text = asyncio.run(run(args.shipment_id))
    print(text or f"No analysis produced for {args.shipment_id}.")


if __name__ == "__main__":
    main()