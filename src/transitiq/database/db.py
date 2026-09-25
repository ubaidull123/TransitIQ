from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from transitiq.database.config import settings


database_url = settings.database_url


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
