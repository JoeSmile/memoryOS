"""In-flight token quota reservations (Redis + single-process fallback)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_LOCAL_TOTAL: dict[str, int] = {}
_LOCAL_STREAM: dict[str, int] = {}
_LOCAL_MUTEX = asyncio.Lock()

_RESERVE_LUA = """
local total_key = KEYS[1]
local stream_key = KEYS[2]
local pg_used = tonumber(ARGV[1])
local amount = tonumber(ARGV[2])
local quota = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

local reserved = tonumber(redis.call('GET', total_key) or '0')
if pg_used + reserved + amount > quota then
  return 0
end
redis.call('INCRBY', total_key, amount)
redis.call('EXPIRE', total_key, ttl)
redis.call('SET', stream_key, amount, 'EX', ttl)
return 1
"""

_RELEASE_LUA = """
local total_key = KEYS[1]
local stream_key = KEYS[2]
local amount = redis.call('GET', stream_key)
if amount == false then
  return 0
end
redis.call('DECRBY', total_key, amount)
redis.call('DEL', stream_key)
return 1
"""


def token_quota_reserved_total_key(user_id: uuid.UUID, day: date) -> str:
    return f"memoryos:quota:rsv:total:{user_id}:{day.isoformat()}"


def token_quota_reserved_stream_key(stream_id: str) -> str:
    return f"memoryos:quota:rsv:stream:{stream_id}"


def quota_reserve_amount() -> int:
    return min(
        settings.token_quota_request_reserve,
        settings.user_daily_token_quota,
    )


def seconds_until_utc_day_end(day: date) -> int:
    day_start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    now = datetime.now(timezone.utc)
    remaining = int((day_end - now).total_seconds()) + 60
    return max(remaining, 3600)


class TokenQuotaReserve:
    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis
        self._reserve_sha: str | None = None
        self._release_sha: str | None = None

    async def _ensure_scripts(self) -> tuple[str, str]:
        if self.redis is None:
            raise RuntimeError("redis required")
        if self._reserve_sha is None or self._release_sha is None:
            self._reserve_sha = await self.redis.script_load(_RESERVE_LUA)
            self._release_sha = await self.redis.script_load(_RELEASE_LUA)
        return self._reserve_sha, self._release_sha

    async def try_reserve(
        self,
        *,
        user_id: uuid.UUID,
        day: date,
        stream_id: str,
        pg_used: int,
    ) -> bool:
        amount = quota_reserve_amount()
        quota = settings.user_daily_token_quota
        if pg_used + amount > quota:
            return False

        if self.redis is not None:
            try:
                reserve_sha, _ = await self._ensure_scripts()
                total_key = token_quota_reserved_total_key(user_id, day)
                stream_key = token_quota_reserved_stream_key(stream_id)
                ttl = seconds_until_utc_day_end(day)
                result = await self.redis.evalsha(
                    reserve_sha,
                    2,
                    total_key,
                    stream_key,
                    pg_used,
                    amount,
                    quota,
                    ttl,
                )
                return bool(result)
            except Exception:
                logger.debug("token quota reserve redis failed", exc_info=True)

        local_total_key = f"{user_id}:{day.isoformat()}"
        async with _LOCAL_MUTEX:
            reserved = _LOCAL_TOTAL.get(local_total_key, 0)
            if pg_used + reserved + amount > quota:
                return False
            _LOCAL_TOTAL[local_total_key] = reserved + amount
            _LOCAL_STREAM[stream_id] = amount
            return True

    async def release(self, *, user_id: uuid.UUID, day: date, stream_id: str) -> None:
        if self.redis is not None:
            try:
                _, release_sha = await self._ensure_scripts()
                total_key = token_quota_reserved_total_key(user_id, day)
                stream_key = token_quota_reserved_stream_key(stream_id)
                await self.redis.evalsha(release_sha, 2, total_key, stream_key)
            except Exception:
                logger.debug("token quota release redis failed", exc_info=True)

        local_total_key = f"{user_id}:{day.isoformat()}"
        async with _LOCAL_MUTEX:
            amount = _LOCAL_STREAM.pop(stream_id, None)
            if amount is None:
                return
            reserved = _LOCAL_TOTAL.get(local_total_key, 0)
            _LOCAL_TOTAL[local_total_key] = max(reserved - amount, 0)
