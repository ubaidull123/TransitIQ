import asyncio
from os import getenv

import uvicorn


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    """Use the selector loop, which psycopg's async connections require on Windows."""
    return asyncio.SelectorEventLoop()


def main() -> None:
    uvicorn.run(
        "transitiq.api.app:app",
        host=getenv("API_HOST", "127.0.0.1"),
        port=int(getenv("API_PORT", "8765")),
        loop=selector_loop_factory,
    )


if __name__ == "__main__":
    main()