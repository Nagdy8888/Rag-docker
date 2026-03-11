"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # OpenAI
    openai_api_key: str = ""

    # Database (Supabase Postgres connection URI)
    database_uri: str = ""

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "rag-agent"

    # App
    documents_path: str = "documents"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
