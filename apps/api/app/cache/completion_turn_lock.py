"""In-flight guard for duplicate client_message_id concurrent SSE."""

import asyncio
import logging
import uuid

from redis.asyncio import Redis

from app.cache.keys import completion_turn_inflight_key

logger = logging.getLogger(__name__)

# Harness / no-Redis dev: single-process fallback
_LOCAL_KEYS: set[str] = set()
_LOCAL_MUTEX = asyncio.Lock()

# BFF maxDuration=60s; add headroom for slow clients
_INFLIGHT_TTL_SECONDS = 120


class CompletionTurnLock:
    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    async def try_acquire(
        self,
        conversation_id: uuid.UUID,
        client_message_id: uuid.UUID,
    ) -> bool:
        key = completion_turn_inflight_key(conversation_id, client_message_id)
        if self.redis is not None:
            try:
                acquired = await self.redis.set(
                    key,
                    "1",
                    nx=True,
                    ex=_INFLIGHT_TTL_SECONDS,
                )
                if acquired:
                    return True
                return False
            except Exception:
                logger.debug("completion turn lock redis acquire failed", exc_info=True)

        async with _LOCAL_MUTEX:
            if key in _LOCAL_KEYS:
                return False
            _LOCAL_KEYS.add(key)
            return True

    async def release(
        self,
        conversation_id: uuid.UUID,
        client_message_id: uuid.UUID,
    ) -> None:
        key = completion_turn_inflight_key(conversation_id, client_message_id)
        if self.redis is not None:
            try:
                await self.redis.delete(key)
            except Exception:
                logger.debug("completion turn lock redis release failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_KEYS.discard(key)
