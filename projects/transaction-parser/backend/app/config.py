"""Application configuration, read from environment variables / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the transaction-parser backend.

    All values are sourced from the process environment (populated by
    docker compose from the repo-root `.env` file). See `.env.example`.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@db:5432/transaction_parser"
    )
    app_env: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (env read once per process)."""
    return Settings()
