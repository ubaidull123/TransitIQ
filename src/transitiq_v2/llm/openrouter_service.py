from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_MODEL = "deepseek/deepseek-v4-flash-0731"


def get_openrouter_client() -> ChatOpenRouter:
    """
    Returns an instance of the ChatOpenRouter client.
    """
    return ChatOpenRouter(model=OPENROUTER_MODEL)
