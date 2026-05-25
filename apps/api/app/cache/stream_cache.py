import logging
import uuid

from redis.asyncio import Redis

from app.cache.keys import stream_key
from app.core.config import settings

logger = logging.getLogger(__name__)


class StreamCache:
    """EP02 SSE 流式 partial content 临时缓冲（Story 3.3 基础设施）。"""

    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis
        self.ttl = settings.stream_cache_ttl

    @property
    def enabled(self) -> bool:
        return self.redis is not None

    async def append(
        self,
        conversation_id: uuid.UUID,
        stream_id: str,
        chunk: str,
    ) -> None:
        if not self.enabled or not chunk:
            return
        key = stream_key(conversation_id, stream_id)
        try:
            pipe = self.redis.pipeline()
            await pipe.append(key, chunk)
            await pipe.expire(key, self.ttl)
            await pipe.execute()
        except Exception:
            logger.debug("stream cache append failed", exc_info=True)

    async def get(self, conversation_id: uuid.UUID, stream_id: str) -> str:
        if not self.enabled:
            return ""
        try:
            value = await self.redis.get(stream_key(conversation_id, stream_id))
            return value or ""
        except Exception:
            logger.debug("stream cache get failed", exc_info=True)
            return ""

    async def delete(self, conversation_id: uuid.UUID, stream_id: str) -> None:
        if not self.enabled:
            return
        try:
            await self.redis.delete(stream_key(conversation_id, stream_id))
        except Exception:
            logger.debug("stream cache delete failed", exc_info=True)
