from collections.abc import Callable

from transitiq.database.db import get_connection


class TicketRepository:
    columns = "shipment_id, origin, destination, carrier, issue_description, created_at"

    def __init__(self, connection_context: Callable = get_connection) -> None:
        self.connection_context = connection_context

    async def create(self, data: dict) -> dict:
        async with self.connection_context() as connection:
            cursor = await connection.execute(
                f"""
                INSERT INTO issues (origin, destination, carrier, issue_description)
                VALUES (%s, %s, %s, %s)
                RETURNING {self.columns}
                """,
                (data["origin"], data["destination"], data["carrier"], data["issue_description"]),
            )
            ticket = await cursor.fetchone()
        return dict(ticket)

    async def get(self, shipment_id: int) -> dict | None:
        async with self.connection_context() as connection:
            cursor = await connection.execute(
                f"SELECT {self.columns} FROM issues WHERE shipment_id = %s",
                (shipment_id,),
            )
            ticket = await cursor.fetchone()
        return dict(ticket) if ticket else None

    async def list_ids(self) -> list[int]:
        async with self.connection_context() as connection:
            cursor = await connection.execute(
                "SELECT shipment_id FROM issues ORDER BY shipment_id ASC"
            )
            rows = await cursor.fetchall()
        return [row["shipment_id"] for row in rows]

    async def list_tickets(self) -> list[dict]:
        async with self.connection_context() as connection:
            cursor = await connection.execute(
                f"SELECT {self.columns} FROM issues ORDER BY shipment_id ASC"
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]


ticket_repository = TicketRepository()
