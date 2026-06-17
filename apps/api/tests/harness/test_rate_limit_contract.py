"""L1 Harness：限流契约（42901，需 Redis）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import rate_limit as rate_limit_module
from app.core.config import settings
from app.core.redis import create_redis_client, discard_redis, ping_redis
from app.main import app


@pytest.fixture
async def rate_limit_redis():
    if not settings.redis_url:
        pytest.skip("REDIS_URL not configured")

    discard_redis()
    rate_limit_module._script_sha = None
    redis = create_redis_client()
    if redis is None or not await ping_redis(redis):
        pytest.skip("Redis not available (run pnpm db:up)")

    await redis.flushdb()
    await redis.aclose()
    try:
        yield
    finally:
        rate_limit_module._script_sha = None
        cleanup = create_redis_client()
        if cleanup is not None:
            await cleanup.flushdb()
            await cleanup.aclose()
        discard_redis()


@pytest.fixture
def rate_limit_enabled(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_fail_open", False)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"rl-{uuid.uuid4()}@example.com"
    password = "harness-password-8"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert reg.status_code == 200
    user_id = reg.json()["data"]["id"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return token, user_id


@pytest.mark.asyncio
async def test_login_rate_limit_returns_42901(
    rate_limit_redis, rate_limit_enabled, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_login_per_ip_per_min", 2)

    transport = ASGITransport(app=app)
    payload = {"email": "nobody@example.com", "password": "wrong-password"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(2):
            resp = await client.post("/api/v1/auth/login", json=payload)
            assert resp.status_code == 401

        limited = await client.post("/api/v1/auth/login", json=payload)
        assert limited.status_code == 429
        body = limited.json()
        assert body["code"] == 42901
        assert body["message"] == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_chat_completions_rate_limit_returns_42901(
    rate_limit_redis, rate_limit_enabled, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_chat_per_min", 2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        body = {
            "conversation_id": str(uuid.uuid4()),
            "content": "你好",
        }

        for _ in range(2):
            resp = await client.post(
                "/api/v1/chat/completions",
                headers=headers,
                json=body,
            )
            # Rate limit runs before handler; unknown conversation fails fast after count.
            assert resp.status_code == 404

        limited = await client.post(
            "/api/v1/chat/completions",
            headers=headers,
            json=body,
        )
        assert limited.status_code == 429
        payload = limited.json()
        assert payload["code"] == 42901
        assert payload["message"] == "rate_limit_exceeded"
