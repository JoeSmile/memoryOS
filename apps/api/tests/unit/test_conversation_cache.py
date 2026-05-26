"""ConversationCache 单元测试（需本地 Redis）。"""

import uuid
from datetime import datetime, timezone

import pytest

from app.cache.conversation_cache import ConversationCache
from app.cache.keys import conversation_list_key
from app.core.redis import create_redis_client, ping_redis
from app.models import Conversation


@pytest.fixture
async def redis_client():
    client = create_redis_client()
    if client is None or not await ping_redis(client):
        pytest.skip("Redis not available (run pnpm db:up and set REDIS_URL)")
    yield client
    await client.flushdb()
    await client.aclose()


def _sample_conversation(user_id: uuid.UUID, title: str = "Cached chat") -> Conversation:
    now = datetime.now(timezone.utc)
    return Conversation(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_conversation_cache_miss_then_hit(redis_client):
    user_id = uuid.uuid4()
    cache = ConversationCache(redis_client)

    assert await cache.get_list(user_id) is None

    rows = [_sample_conversation(user_id, "A"), _sample_conversation(user_id, "B")]
    await cache.set_list(user_id, rows)

    cached = await cache.get_list(user_id)
    assert cached is not None
    assert len(cached) == 2
    assert cached[0].title == "A"
    assert cached[1].title == "B"


@pytest.mark.asyncio
async def test_conversation_cache_invalidate(redis_client):
    user_id = uuid.uuid4()
    cache = ConversationCache(redis_client)
    await cache.set_list(user_id, [_sample_conversation(user_id)])

    assert await cache.get_list(user_id) is not None

    await cache.invalidate(user_id)
    assert await redis_client.get(conversation_list_key(user_id)) is None
    assert await cache.get_list(user_id) is None


@pytest.mark.asyncio
async def test_conversation_cache_disabled_when_no_client():
    cache = ConversationCache(None)
    user_id = uuid.uuid4()
    assert await cache.get_list(user_id) is None
    await cache.set_list(user_id, [_sample_conversation(user_id)])
    assert await cache.get_list(user_id) is None
