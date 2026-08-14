"""Application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    app_name: str = "Agentic RAG Assistant"
    app_version: str = "0.1.0"
    app_description: str = "Production-grade Agentic RAG Assistant"

    environment: str = "development"
    debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000

    secret_key: str = "CHANGE_ME"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    openai_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic_rag"
    )

    redis_url: str = "redis://localhost:6379/0"

    chroma_persist_directory: str = "./data/chroma"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
