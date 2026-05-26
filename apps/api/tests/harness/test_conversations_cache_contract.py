"""L1 Harness：创建会话后列表包含新会话（验证 commit 后缓存失效）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.cache.keys import conversation_list_key
from app.core.config import settings
from app.core.redis import create_redis_client, ping_redis
from app.main import app


@pytest.mark.asyncio
async def test_create_conversation_invalidates_list_cache():
    if not settings.redis_url:
        pytest.skip("REDIS_URL not configured")

    redis = create_redis_client()
    if redis is None or not await ping_redis(redis):
        pytest.skip("Redis not available (run pnpm db:up)")
    await redis.flushdb()

    transport = ASGITransport(app=app)
    email = f"cache-{uuid.uuid4()}@example.com"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            user_resp = await client.post("/api/v1/users", json={"email": email})
            assert user_resp.status_code == 200
            user_id = user_resp.json()["data"]["id"]

            list_resp = await client.get(
                "/api/v1/conversations",
                params={"user_id": user_id},
            )
            assert list_resp.status_code == 200
            assert list_resp.json()["data"] == []

            cache_key = conversation_list_key(uuid.UUID(user_id))
            assert await redis.get(cache_key) is not None

            create_resp = await client.post(
                "/api/v1/conversations",
                json={"user_id": user_id, "title": "After invalidate"},
            )
            assert create_resp.status_code == 200
            conv_id = create_resp.json()["data"]["id"]

            assert await redis.get(cache_key) is None

            list_resp2 = await client.get(
                "/api/v1/conversations",
                params={"user_id": user_id},
            )
            assert list_resp2.status_code == 200
            ids = [c["id"] for c in list_resp2.json()["data"]]
            assert conv_id in ids
    finally:
        await redis.flushdb()
        await redis.aclose()
