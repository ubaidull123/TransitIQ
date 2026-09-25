import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


class Settings:
    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            database=os.environ["DB_NAME"],
        )


settings = Settings()
