"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """All environment variables consumed by the application.

    Values are loaded from a .env file (if present) and can be overridden
    by real environment variables at runtime.
    """

    # TigerGraph
    tigergraph_host: str = ""
    tigergraph_username: str = ""
    tigergraph_password: str = ""
    tigergraph_secret: str = ""
    tigergraph_graph_name_person: str = "PersonGraph"
    tigergraph_graph_name_dep: str = "DepGraph"

    # Groq
    groq_api_key: str = ""

    # LinkedIn
    linkedin_username: str = ""
    linkedin_password: str = ""

    # GitHub
    github_token: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    # Demo / mock mode — set to true to bypass LinkedIn auth entirely
    demo_mode: bool = True

    model_config = {"env_file": str(ENV_FILE), "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()
