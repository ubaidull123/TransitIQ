import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import getenv
import sys

from dotenv import load_dotenv
from psycopg import AsyncConnection
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

load_dotenv()


def get_database_uri() -> str:
    """Return the PostgreSQL connection URI from environment variables."""
    test_uri = getenv("TEST_DATABASE_URL")
    if test_uri:
        return test_uri

    settings = {
        "host": getenv("DB_HOST"),
        "dbname": getenv("DB_NAME"),
        "user": getenv("DB_USER"),
        "password": getenv("DB_PASSWORD"),
        "port": getenv("DB_PORT"),
    }
    missing = [name for name, value in settings.items() if not value]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL settings: {', '.join(missing)}")
    return make_conninfo(**settings)


@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection]:
    """Provide an async PostgreSQL connection context."""
    connection = await AsyncConnection.connect(get_database_uri(), row_factory=dict_row)
    try:
        yield connection
        await connection.commit()
    except Exception:
        await connection.rollback()
        raise
    finally:
        await connection.close()


async def initialize_ticket_schema() -> None:
    """Create only the immutable ticket-ingress issues table."""
    async with get_connection() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                shipment_id SERIAL PRIMARY KEY,
                origin VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                carrier VARCHAR(255) NOT NULL,
                issue_description TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await connection.execute(
            "ALTER TABLE issues ADD COLUMN IF NOT EXISTS created_at "
            "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )
