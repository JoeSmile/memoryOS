"""Sliding-window rate limiter unit tests (EP09 3.1)."""

import uuid

import pytest
from redis.asyncio import Redis

from app.core import rate_limit as rate_limit_module
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.rate_limit import (
    RouteClass,
    assert_rate_limit_allowed,
    check_rate_limit,
    ip_identity,
    rate_limit_redis_key,
    user_identity,
)
from app.core.redis import create_redis_client, ping_redis


@pytest.fixture(autouse=True)
def reset_rate_limit_script_sha():
    rate_limit_module._script_sha = None
    yield
    rate_limit_module._script_sha = None


@pytest.fixture
async def redis_client():
    client = create_redis_client()
    if client is None or not await ping_redis(client):
        pytest.skip("Redis not available (run pnpm db:up)")
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.mark.asyncio
async def test_rate_limit_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    decision = await check_rate_limit(
        None,
        route_class=RouteClass.CHAT,
        identity=user_identity(str(uuid.uuid4())),
    )
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_rate_limit_fail_open_without_redis(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_fail_open", True)
    decision = await check_rate_limit(
        None,
        route_class=RouteClass.LOGIN,
        identity=ip_identity("203.0.113.1"),
    )
    assert decision.allowed is True
    assert decision.degraded is True


@pytest.mark.asyncio
async def test_rate_limit_fail_closed_without_redis_returns_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_fail_open", False)
    decision = await check_rate_limit(
        None,
        route_class=RouteClass.CHAT,
        identity=user_identity(str(uuid.uuid4())),
    )
    assert decision.allowed is False
    assert decision.unavailable is True


@pytest.mark.asyncio
async def test_assert_rate_limit_raises_50302_when_redis_missing_and_fail_closed(
    monkeypatch,
):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_fail_open", False)
    with pytest.raises(AppException) as exc:
        await assert_rate_limit_allowed(
            None,
            route_class=RouteClass.CHAT,
            identity=user_identity(str(uuid.uuid4())),
        )
    assert exc.value.code == 50302
    assert exc.value.message == "rate_limit_unavailable"


@pytest.mark.asyncio
async def test_sliding_window_allows_under_limit(redis_client: Redis, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_chat_per_min", 3)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    identity = user_identity(str(uuid.uuid4()))

    for _ in range(3):
        decision = await check_rate_limit(
            redis_client,
            route_class=RouteClass.CHAT,
            identity=identity,
        )
        assert decision.allowed is True


@pytest.mark.asyncio
async def test_sliding_window_blocks_over_limit(redis_client: Redis, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_chat_per_min", 2)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    identity = user_identity(str(uuid.uuid4()))

    assert (
        await check_rate_limit(
            redis_client, route_class=RouteClass.CHAT, identity=identity
        )
    ).allowed
    assert (
        await check_rate_limit(
            redis_client, route_class=RouteClass.CHAT, identity=identity
        )
    ).allowed

    with pytest.raises(AppException) as exc:
        await assert_rate_limit_allowed(
            redis_client,
            route_class=RouteClass.CHAT,
            identity=identity,
        )
    assert exc.value.code == 42901
    assert exc.value.message == "rate_limit_exceeded"


def test_rate_limit_redis_key_format():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    assert rate_limit_redis_key(RouteClass.CHAT, user_identity(uid)) == (
        f"rl:chat:user:{uid}"
    )
    assert rate_limit_redis_key(RouteClass.LOGIN, ip_identity("203.0.113.42")) == (
        "rl:login:ip:203.0.113.42"
    )


def test_client_ip_prefers_x_forwarded_for_when_proxy_trusted(monkeypatch):
    from starlette.requests import Request

    from app.core.rate_limit import client_ip

    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "server": ("test", 80),
        "scheme": "http",
        "http_version": "1.1",
    }
    request = Request(scope)
    assert client_ip(request) == "203.0.113.9"


def test_client_ip_ignores_x_forwarded_for_when_proxy_untrusted(monkeypatch):
    from starlette.requests import Request

    from app.core.rate_limit import client_ip

    monkeypatch.setattr(settings, "trust_proxy_headers", False)
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "server": ("test", 80),
        "scheme": "http",
        "http_version": "1.1",
    }
    request = Request(scope)
    assert client_ip(request) == "127.0.0.1"


def test_client_ip_falls_back_to_request_client_host():
    from starlette.requests import Request

    from app.core.rate_limit import client_ip

    scope = {
        "type": "http",
        "headers": [],
        "client": ("198.51.100.4", 54321),
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "server": ("test", 80),
        "scheme": "http",
        "http_version": "1.1",
    }
    request = Request(scope)
    assert client_ip(request) == "198.51.100.4"
