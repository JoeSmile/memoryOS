"""StreamCache 单元测试（可用 fakeredis 或本地 Redis）。"""

import uuid

import pytest

from app.cache.stream_cache import StreamCache
from app.core.redis import create_redis_client, ping_redis


@pytest.fixture
async def redis_client():
    client = create_redis_client()
    if client is None or not await ping_redis(client):
        pytest.skip("Redis not available (run pnpm db:up)")
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.mark.asyncio
async def test_stream_cache_append_get_delete(redis_client):
    cache = StreamCache(redis_client)
    conv_id = uuid.uuid4()
    stream_id = "harness-stream-1"

    await cache.append(conv_id, stream_id, "Hello ")
    await cache.append(conv_id, stream_id, "world")

    assert await cache.get(conv_id, stream_id) == "Hello world"

    await cache.delete(conv_id, stream_id)
    assert await cache.get(conv_id, stream_id) == ""


@pytest.mark.asyncio
async def test_stream_cache_disabled_when_no_client():
    cache = StreamCache(None)
    conv_id = uuid.uuid4()
    await cache.append(conv_id, "x", "chunk")
    assert await cache.get(conv_id, "x") == ""
