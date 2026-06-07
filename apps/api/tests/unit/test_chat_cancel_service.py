"""ChatService.cancel_stream ownership and idempotency."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AppException
from app.services.chat_service import ChatService


def test_interrupted_content_prefers_visible_length_for_long_prefix():
    full = "你好！" * 5000
    assert ChatService._interrupted_content(full, None, visible_length=3) == "你好！"


@pytest.mark.asyncio
async def test_cancel_returns_404_when_active_gone_even_if_cancel_flag_set():
    """Reject replay when stream_active TTL cleared but stream_cancel remains."""
    service = ChatService(AsyncMock(), redis=None)
    service.cancel_cache.get_active_owner = AsyncMock(return_value=None)
    service.cancel_cache.is_cancelled = AsyncMock(return_value=True)

    with pytest.raises(AppException) as exc_info:
        await service.cancel_stream(
            stream_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "stream_not_found"
    service.cancel_cache.is_cancelled.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_idempotent_when_owner_still_active():
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    stream_id = str(uuid.uuid4())

    service = ChatService(AsyncMock(), redis=None)
    service.cancel_cache.get_active_owner = AsyncMock(
        return_value=(conversation_id, user_id),
    )
    service.cancel_cache.is_cancelled = AsyncMock(return_value=True)
    service.cancel_cache.set_cancelled = AsyncMock()

    await service.cancel_stream(stream_id=stream_id, user_id=user_id)

    service.cancel_cache.set_cancelled.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_rejects_foreign_owner():
    owner_id = uuid.uuid4()
    foreign_id = uuid.uuid4()

    service = ChatService(AsyncMock(), redis=None)
    service.cancel_cache.get_active_owner = AsyncMock(
        return_value=(uuid.uuid4(), owner_id),
    )
    service.cancel_cache.is_cancelled = AsyncMock(return_value=False)

    with pytest.raises(AppException) as exc_info:
        await service.cancel_stream(stream_id=str(uuid.uuid4()), user_id=foreign_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_cancel_idempotent_updates_visible_snapshot():
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    stream_id = str(uuid.uuid4())

    service = ChatService(AsyncMock(), redis=None)
    service.cancel_cache.get_active_owner = AsyncMock(
        return_value=(conversation_id, user_id),
    )
    service.cancel_cache.is_cancelled = AsyncMock(return_value=True)
    service.cancel_cache.set_cancelled = AsyncMock()
    service.cancel_cache.update_visible_snapshot = AsyncMock()

    await service.cancel_stream(
        stream_id=stream_id,
        user_id=user_id,
        visible_length=128,
    )

    service.cancel_cache.set_cancelled.assert_not_awaited()
    service.cancel_cache.update_visible_snapshot.assert_awaited_once_with(
        stream_id,
        visible_content=None,
        visible_length=128,
    )


def test_interrupted_content_empty_length_yields_empty_string():
    assert ChatService._interrupted_content("你好", None, visible_length=0) == ""
