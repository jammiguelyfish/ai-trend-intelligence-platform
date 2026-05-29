"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    app_name: str = "ai-trend-intelligence"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./data/trends.db"

    chroma_persist_dir: str = "./data/chroma"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    scrape_user_agent: str = "ai-trend-intelligence/1.0"
    scrape_request_delay: float = 1.0

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
