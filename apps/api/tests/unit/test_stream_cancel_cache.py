"""StreamCancelCache local fallback (no Redis)."""

import uuid

import pytest

from app.cache.stream_cancel_cache import StreamCancelCache


@pytest.mark.asyncio
async def test_register_owner_and_cancel_idempotent():
    stream_id = str(uuid.uuid4())
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    cache = StreamCancelCache(redis=None)

    await cache.register_active(stream_id, conversation_id, user_id)
    assert await cache.get_active_owner(stream_id) == (conversation_id, user_id)
    assert await cache.is_cancelled(stream_id) is False

    await cache.set_cancelled(stream_id)
    assert await cache.is_cancelled(stream_id) is True
    await cache.set_cancelled(stream_id)
    assert await cache.is_cancelled(stream_id) is True

    await cache.clear(stream_id)
    assert await cache.get_active_owner(stream_id) is None
    assert await cache.is_cancelled(stream_id) is False


@pytest.mark.asyncio
async def test_cancel_stores_visible_content_until_clear():
    stream_id = str(uuid.uuid4())
    cache = StreamCancelCache(redis=None)

    await cache.set_cancelled(stream_id, visible_content="你")
    assert await cache.is_cancelled(stream_id) is True
    assert await cache.get_visible_content(stream_id) == "你"

    await cache.clear(stream_id)
    assert await cache.get_visible_content(stream_id) is None


@pytest.mark.asyncio
async def test_cancel_stores_visible_length_until_clear():
    stream_id = str(uuid.uuid4())
    cache = StreamCancelCache(redis=None)

    await cache.set_cancelled(stream_id, visible_length=12_480)
    assert await cache.get_visible_length(stream_id) == 12_480

    await cache.clear(stream_id)
    assert await cache.get_visible_length(stream_id) is None


@pytest.mark.asyncio
async def test_update_visible_snapshot_without_cancel_flag():
    stream_id = str(uuid.uuid4())
    cache = StreamCancelCache(redis=None)

    await cache.update_visible_snapshot(stream_id, visible_length=42)
    assert await cache.is_cancelled(stream_id) is False
    assert await cache.get_visible_length(stream_id) == 42
