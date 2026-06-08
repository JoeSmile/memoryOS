"""In-flight guard: one World Cup ingest per stem at a time (subset vs full overlap safe)."""

import asyncio
import logging

from redis.asyncio import Redis

from app.cache.keys import worldcup_ingest_stem_lock_key

logger = logging.getLogger(__name__)

_LOCAL_KEYS: set[str] = set()
_LOCAL_MUTEX = asyncio.Lock()

# Full Gold live ingest can run ~30+ minutes; TTL avoids dead lock if process crashes.
_INGEST_LOCK_TTL_SECONDS = 3600


class WorldcupIngestLock:
    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    async def try_acquire(self, stems: tuple[str, ...]) -> bool:
        ordered = sorted(set(stems))
        acquired: list[str] = []
        for stem in ordered:
            key = worldcup_ingest_stem_lock_key(stem)
            if not await self._acquire_one(key):
                await self._release_keys(acquired)
                return False
            acquired.append(key)
        return True

    async def release(self, stems: tuple[str, ...]) -> None:
        keys = [worldcup_ingest_stem_lock_key(stem) for stem in sorted(set(stems))]
        await self._release_keys(keys)

    async def _acquire_one(self, key: str) -> bool:
        if self.redis is not None:
            try:
                return bool(
                    await self.redis.set(
                        key, "1", nx=True, ex=_INGEST_LOCK_TTL_SECONDS
                    )
                )
            except Exception:
                logger.warning(
                    "worldcup ingest lock redis acquire failed; falling back to local",
                    exc_info=True,
                )

        async with _LOCAL_MUTEX:
            if key in _LOCAL_KEYS:
                return False
            _LOCAL_KEYS.add(key)
            return True

    async def _release_keys(self, keys: list[str]) -> None:
        for key in keys:
            if self.redis is not None:
                try:
                    await self.redis.delete(key)
                except Exception:
                    logger.debug(
                        "worldcup ingest lock redis release failed", exc_info=True
                    )
            async with _LOCAL_MUTEX:
                _LOCAL_KEYS.discard(key)
