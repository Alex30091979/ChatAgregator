import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://chat_aggregator:chat_aggregator@localhost:5432/chat_aggregator",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

