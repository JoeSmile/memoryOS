"""Redis sliding-window rate limiter (EP09 Story 9.4 task 3.1)."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from fastapi import Depends, Request
from redis.asyncio import Redis
from redis.exceptions import NoScriptError, RedisError

from app.core.config import settings
from app.core.deps import get_current_user_id
from app.core.exceptions import AppException
from app.core.redis import ensure_redis, get_redis

logger = logging.getLogger(__name__)

_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local min_score = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, min_score)
local count = redis.call('ZCARD', key)
if count >= limit then
  return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window + 5)
return 1
"""

_script_sha: str | None = None


class RouteClass(StrEnum):
    CHAT = "chat"
    DEMO_TURN = "demo_turn"
    LOGIN = "login"
    REGISTER = "register"


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    degraded: bool = False
    unavailable: bool = False


def rate_limit_redis_key(route_class: RouteClass, identity: str) -> str:
    """Build shared Redis key: rl:{route_class}:{identity}."""
    return f"rl:{route_class.value}:{identity}"


def user_identity(user_id: str) -> str:
    return f"user:{user_id}"


def ip_identity(ip_address: str) -> str:
    return f"ip:{ip_address}"


def limit_for_route(route_class: RouteClass) -> int:
    match route_class:
        case RouteClass.CHAT:
            return settings.rate_limit_chat_per_min
        case RouteClass.DEMO_TURN:
            return settings.rate_limit_demo_turn_per_min
        case RouteClass.LOGIN:
            return settings.rate_limit_login_per_ip_per_min
        case RouteClass.REGISTER:
            return settings.rate_limit_register_per_ip_per_min


async def _eval_sliding_window(
    redis: Redis,
    *,
    key: str,
    limit: int,
    request_id: str,
) -> bool:
    global _script_sha
    now = int(time.time())
    member = f"{now}:{request_id}"
    window = settings.rate_limit_window_seconds

    async def _run_evalsha() -> object:
        assert _script_sha is not None
        return await redis.evalsha(
            _script_sha,
            1,
            key,
            str(now),
            str(window),
            str(limit),
            member,
        )

    if _script_sha is None:
        _script_sha = await redis.script_load(_SLIDING_WINDOW_LUA)
    try:
        result = await _run_evalsha()
    except NoScriptError:
        _script_sha = await redis.script_load(_SLIDING_WINDOW_LUA)
        result = await _run_evalsha()
    return bool(result)


async def check_rate_limit(
    redis: Redis | None,
    *,
    route_class: RouteClass,
    identity: str,
    request_id: str | None = None,
) -> RateLimitDecision:
    """Return allow/deny without raising; use assert_rate_limit_allowed to enforce."""
    if not settings.rate_limit_enabled:
        return RateLimitDecision(allowed=True)

    if redis is None:
        return _redis_unavailable_decision()

    key = rate_limit_redis_key(route_class, identity)
    limit = limit_for_route(route_class)
    rid = request_id or uuid4().hex

    try:
        allowed = await _eval_sliding_window(
            redis,
            key=key,
            limit=limit,
            request_id=rid,
        )
    except RedisError:
        logger.warning(
            "rate_limit_degraded route=%s identity=%s redis_error",
            route_class.value,
            identity,
            exc_info=True,
        )
        return _redis_unavailable_decision()

    return RateLimitDecision(allowed=allowed)


def _redis_unavailable_decision() -> RateLimitDecision:
    if settings.rate_limit_fail_open:
        return RateLimitDecision(allowed=True, degraded=True)
    return RateLimitDecision(allowed=False, unavailable=True)


async def assert_rate_limit_allowed(
    redis: Redis | None,
    *,
    route_class: RouteClass,
    identity: str,
    request_id: str | None = None,
) -> None:
    """Raise 42901 when limited, or 50302 when Redis is required but unavailable."""
    decision = await check_rate_limit(
        redis,
        route_class=route_class,
        identity=identity,
        request_id=request_id,
    )
    if decision.allowed:
        return
    if decision.unavailable:
        raise AppException(
            code=50302,
            message="rate_limit_unavailable",
            status_code=503,
        )
    raise AppException(
        code=42901,
        message="rate_limit_exceeded",
        status_code=429,
    )


def client_ip(request: Request) -> str:
    """Client IP for rate limit / audit; X-Forwarded-For only when proxy is trusted."""
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


async def enforce_login_rate_limit(
    request: Request,
    redis: Redis | None = Depends(get_redis),
) -> None:
    await assert_rate_limit_allowed(
        redis,
        route_class=RouteClass.LOGIN,
        identity=ip_identity(client_ip(request)),
    )


async def enforce_register_rate_limit(
    request: Request,
    redis: Redis | None = Depends(get_redis),
) -> None:
    await assert_rate_limit_allowed(
        redis,
        route_class=RouteClass.REGISTER,
        identity=ip_identity(client_ip(request)),
    )


async def enforce_chat_rate_limit(
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    redis = await ensure_redis()
    await assert_rate_limit_allowed(
        redis,
        route_class=RouteClass.CHAT,
        identity=user_identity(str(user_id)),
    )


async def enforce_demo_turn_rate_limit(
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    redis = await ensure_redis()
    await assert_rate_limit_allowed(
        redis,
        route_class=RouteClass.DEMO_TURN,
        identity=user_identity(str(user_id)),
    )
