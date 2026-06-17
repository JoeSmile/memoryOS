import logging
from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


def discard_redis() -> None:
    """Drop cached client without closing (safe when the event loop may be closed)."""
    global _redis
    _redis = None


def create_redis_client() -> Redis | None:
    if not settings.redis_url:
        return None
    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def ensure_redis() -> Redis | None:
    """懒加载共享连接，供 Depends 与健康检查复用。"""
    global _redis
    if not settings.redis_url:
        return None
    if _redis is None:
        _redis = create_redis_client()
    return _redis


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    yield await ensure_redis()


async def close_redis() -> None:
    global _redis
    if _redis is None:
        return
    try:
        await _redis.aclose()
    except RuntimeError:
        # pytest may tear down the event loop before fixture teardown runs.
        logger.debug("Redis close skipped (event loop closed)", exc_info=True)
    except Exception:
        logger.debug("Redis close failed", exc_info=True)
    finally:
        _redis = None


async def ping_redis(client: Redis | None) -> bool:
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception:
        logger.debug("Redis ping failed", exc_info=True)
        return False
