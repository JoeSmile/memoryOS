"""Cancel coordination for in-flight completion streams (Redis or local fallback)."""

import asyncio
import json
import logging
import uuid

from redis.asyncio import Redis

from app.cache.keys import (
    stream_active_key,
    stream_cancel_key,
    stream_cancel_visible_key,
    stream_cancel_visible_len_key,
)

logger = logging.getLogger(__name__)

_STREAM_TTL_SECONDS = 120

_LOCAL_ACTIVE: dict[str, tuple[uuid.UUID, uuid.UUID]] = {}
_LOCAL_CANCELLED: set[str] = set()
_LOCAL_VISIBLE: dict[str, str] = {}
_LOCAL_VISIBLE_LEN: dict[str, int] = {}
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
                if raw is not None:
                    if isinstance(raw, bytes):
                        raw = raw.decode()
                    owner = self._decode_owner(raw)
                    if owner is not None:
                        return owner
            except Exception:
                logger.debug("stream active redis get failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return _LOCAL_ACTIVE.get(stream_id)

    async def set_cancelled(
        self,
        stream_id: str,
        *,
        visible_content: str | None = None,
        visible_length: int | None = None,
    ) -> None:
        key = stream_cancel_key(stream_id)
        visible_key = stream_cancel_visible_key(stream_id)
        visible_len_key = stream_cancel_visible_len_key(stream_id)
        if self.redis is not None:
            try:
                pipe = self.redis.pipeline()
                pipe.set(key, "1", ex=_STREAM_TTL_SECONDS)
                if visible_content is not None:
                    pipe.set(visible_key, visible_content, ex=_STREAM_TTL_SECONDS)
                if visible_length is not None:
                    pipe.set(
                        visible_len_key,
                        str(visible_length),
                        ex=_STREAM_TTL_SECONDS,
                    )
                await pipe.execute()
                return
            except Exception:
                logger.debug("stream cancel redis set failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_CANCELLED.add(stream_id)
            if visible_content is not None:
                _LOCAL_VISIBLE[stream_id] = visible_content
            if visible_length is not None:
                _LOCAL_VISIBLE_LEN[stream_id] = visible_length

    async def update_visible_snapshot(
        self,
        stream_id: str,
        *,
        visible_content: str | None = None,
        visible_length: int | None = None,
    ) -> None:
        visible_key = stream_cancel_visible_key(stream_id)
        visible_len_key = stream_cancel_visible_len_key(stream_id)
        if self.redis is not None:
            try:
                pipe = self.redis.pipeline()
                if visible_content is not None:
                    pipe.set(visible_key, visible_content, ex=_STREAM_TTL_SECONDS)
                if visible_length is not None:
                    pipe.set(
                        visible_len_key,
                        str(visible_length),
                        ex=_STREAM_TTL_SECONDS,
                    )
                if visible_content is not None or visible_length is not None:
                    await pipe.execute()
                return
            except Exception:
                logger.debug("stream cancel visible update failed", exc_info=True)

        async with _LOCAL_MUTEX:
            if visible_content is not None:
                _LOCAL_VISIBLE[stream_id] = visible_content
            if visible_length is not None:
                _LOCAL_VISIBLE_LEN[stream_id] = visible_length

    async def is_cancelled(self, stream_id: str) -> bool:
        key = stream_cancel_key(stream_id)
        if self.redis is not None:
            try:
                if await self.redis.exists(key) > 0:
                    return True
            except Exception:
                logger.debug("stream cancel redis exists failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return stream_id in _LOCAL_CANCELLED

    async def get_visible_content(self, stream_id: str) -> str | None:
        visible_key = stream_cancel_visible_key(stream_id)
        if self.redis is not None:
            try:
                raw = await self.redis.get(visible_key)
                if raw is not None:
                    return raw.decode() if isinstance(raw, bytes) else raw
            except Exception:
                logger.debug("stream cancel visible redis get failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return _LOCAL_VISIBLE.get(stream_id)

    async def get_visible_length(self, stream_id: str) -> int | None:
        visible_len_key = stream_cancel_visible_len_key(stream_id)
        if self.redis is not None:
            try:
                raw = await self.redis.get(visible_len_key)
                if raw is not None:
                    text = raw.decode() if isinstance(raw, bytes) else raw
                    return int(text)
            except (TypeError, ValueError):
                logger.debug("stream cancel visible len parse failed", exc_info=True)
            except Exception:
                logger.debug("stream cancel visible len redis get failed", exc_info=True)

        async with _LOCAL_MUTEX:
            return _LOCAL_VISIBLE_LEN.get(stream_id)

    async def clear(self, stream_id: str) -> None:
        active_key = stream_active_key(stream_id)
        cancel_key = stream_cancel_key(stream_id)
        visible_key = stream_cancel_visible_key(stream_id)
        visible_len_key = stream_cancel_visible_len_key(stream_id)
        if self.redis is not None:
            try:
                await self.redis.delete(
                    active_key,
                    cancel_key,
                    visible_key,
                    visible_len_key,
                )
            except Exception:
                logger.debug("stream cancel redis clear failed", exc_info=True)

        async with _LOCAL_MUTEX:
            _LOCAL_ACTIVE.pop(stream_id, None)
            _LOCAL_CANCELLED.discard(stream_id)
            _LOCAL_VISIBLE.pop(stream_id, None)
            _LOCAL_VISIBLE_LEN.pop(stream_id, None)
