from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_MODEL = "inclusionai/ling-3.0-flash-fin:free"


def get_openrouter_client() -> ChatOpenRouter:
    """
    Returns an instance of the ChatOpenRouter client.
    """
    return ChatOpenRouter(model=OPENROUTER_MODEL)
