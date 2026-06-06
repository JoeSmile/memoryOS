"""CompletionTurnLock local fallback (no Redis)."""

import uuid

import pytest

from app.cache.completion_turn_lock import CompletionTurnLock


@pytest.mark.asyncio
async def test_local_turn_lock_blocks_second_acquire():
    conversation_id = uuid.uuid4()
    client_message_id = uuid.uuid4()
    lock = CompletionTurnLock(redis=None)

    assert await lock.try_acquire(conversation_id, client_message_id) is True
    assert await lock.try_acquire(conversation_id, client_message_id) is False

    await lock.release(conversation_id, client_message_id)
    assert await lock.try_acquire(conversation_id, client_message_id) is True
    await lock.release(conversation_id, client_message_id)
