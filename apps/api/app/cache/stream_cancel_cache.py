"""Cancel coordination for in-flight completion streams (Redis or local fallback)."""

import asyncio
import json
import logging
import uuid

from redis.asyncio import Redis

from app.cache.keys import stream_active_key, stream_cancel_key

logger = logging.getLogger(__name__)

_STREAM_TTL_SECONDS = 120

_LOCAL_ACTIVE: dict[str, tuple[uuid.UUID, uuid.UUID]] = {}
_LOCAL_CANCELLED: set[str] = set()
_LOCAL_MUTEX = asyncio.Lock()


class StreamCancelCache:
    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    @staticmethod
    def _encode_owner(conversation_id: uuid.UUID, user_id: uuid.UUID) -> str:
        return json.dumps(
            {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
            }
        )

    @staticmethod
    def _decode_owner(raw: str) -> tuple[uuid.UUID, uuid.UUID] | None:
        try:
            payload = json.loads(raw)
            return (
                uuid.UUID(payload["conversation_id"]),
                uuid.UUID(payload["user_id"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    async def register_active(
        self,
        stream_id: str,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        key = stream_active_key(stream_id)
        value = self._encode_owner(conversation_id, user_id)
        if self.redis is not None:
            try:
                await self.redis.set(key, value, ex=_STREAM_TTL_SECONDS)
                return
            except Exception:
                logger.debug("stream active redis register failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_ACTIVE[stream_id] = (conversation_id, user_id)

    async def get_active_owner(
        self,
        stream_id: str,
    ) -> tuple[uuid.UUID, uuid.UUID] | None:
        key = stream_active_key(stream_id)
        if self.redis is not None:
            try:
                raw = await self.redis.get(key)
                if raw is None:
                    return None
                if isinstance(raw, bytes):
                    raw = raw.decode()
                return self._decode_owner(raw)
            except Exception:
                logger.debug("stream active redis get failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return _LOCAL_ACTIVE.get(stream_id)

    async def set_cancelled(self, stream_id: str) -> None:
        key = stream_cancel_key(stream_id)
        if self.redis is not None:
            try:
                await self.redis.set(key, "1", ex=_STREAM_TTL_SECONDS)
                return
            except Exception:
                logger.debug("stream cancel redis set failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_CANCELLED.add(stream_id)

    async def is_cancelled(self, stream_id: str) -> bool:
        key = stream_cancel_key(stream_id)
        if self.redis is not None:
            try:
                return await self.redis.exists(key) > 0
            except Exception:
                logger.debug("stream cancel redis exists failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return stream_id in _LOCAL_CANCELLED

    async def clear(self, stream_id: str) -> None:
        active_key = stream_active_key(stream_id)
        cancel_key = stream_cancel_key(stream_id)
        if self.redis is not None:
            try:
                await self.redis.delete(active_key, cancel_key)
            except Exception:
                logger.debug("stream cancel redis clear failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_ACTIVE.pop(stream_id, None)
            _LOCAL_CANCELLED.discard(stream_id)
