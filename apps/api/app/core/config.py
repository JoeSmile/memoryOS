import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MemoryOS API"
    env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str | None = Field(
        default="postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos",
        description="postgresql+asyncpg://user:pass@host:5432/dbname",
    )

    redis_url: str | None = Field(
        default="redis://localhost:6379/0",
        description="redis://host:6379/0 — unset to disable cache",
    )

    conversation_list_cache_ttl: int = Field(
        default=300,
        description="seconds for memoryos:conversations:user:{id}",
    )

    stream_cache_ttl: int = Field(
        default=3600,
        description="seconds for memoryos:stream:{conversation_id}:{stream_id}",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.database_url:
        logger.warning(
            "DATABASE_URL is not set; DB features disabled until configured "
            "(see apps/api/.env.example, run pnpm db:up)."
        )
    if not s.redis_url:
        logger.warning(
            "REDIS_URL is not set; cache features disabled "
            "(see apps/api/.env.example)."
        )
    return s


settings = get_settings()
