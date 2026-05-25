import logging
from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


def create_redis_client() -> Redis | None:
    if not settings.redis_url:
        return None
    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    """Per-request Redis; yields None when REDIS_URL is unset."""
    global _redis
    if not settings.redis_url:
        yield None
        return
    if _redis is None:
        _redis = create_redis_client()
    yield _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def ping_redis(client: Redis | None) -> bool:
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception:
        logger.debug("Redis ping failed", exc_info=True)
        return False
