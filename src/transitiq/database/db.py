from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os
load_dotenv()


database_url = URL.create(
	drivername="postgresql+psycopg",
	username=os.environ["DB_USER"],
	password=os.environ["DB_PASSWORD"],
	host=os.environ["DB_HOST"],
	port=int(os.environ["DB_PORT"]),
	database=os.environ["DB_NAME"],
)


engine = create_async_engine(database_url, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



class Base(DeclarativeBase):
    pass


def get_database_uri() -> str:
    """Libpq DSN for the LangGraph checkpointer; it does not understand SQLAlchemy URLs."""
    return database_url.set(drivername="postgresql").render_as_string(hide_password=False)



async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
