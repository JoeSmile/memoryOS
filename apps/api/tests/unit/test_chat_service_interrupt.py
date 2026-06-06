"""ChatService interrupted assistant persistence."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.message import COMPLETION_INTERRUPTED
from app.services.chat_service import ChatService


class _DisconnectAfterFirstToken:
    def __init__(self) -> None:
        self._calls = 0

    async def is_disconnected(self) -> bool:
        self._calls += 1
        return self._calls > 1


@pytest.mark.asyncio
async def test_stream_persists_interrupted_assistant_on_disconnect(monkeypatch):
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    user_row = MagicMock()
    user_row.id = uuid.uuid4()
    user_row.role = "user"
    user_row.content = "hi"

    assistant_row = MagicMock()
    assistant_row.id = uuid.uuid4()
    assistant_row.role = "assistant"
    assistant_row.content = "你"
    assistant_row.completion_status = COMPLETION_INTERRUPTED

    service = ChatService(db, redis=None, runner=MagicMock())

    service.conversations.get_owned_conversation = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    async def fake_stream(*_args, **_kwargs):
        yield "你"
        yield "好"

    service.runner.stream_tokens = fake_stream

    request = MagicMock()
    request.is_disconnected = _DisconnectAfterFirstToken().is_disconnected

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    events = []
    async for event in service.stream_completion_events(
        stream_state=stream_state,
        request=request,
    ):
        events.append(event)

    await service.finalize_completion_stream(stream_state)

    assert len(events) == 1
    assert events[0]["event"] == "token"
    service.messages.create.assert_called_once()
    call_args, call_kwargs = service.messages.create.call_args
    assert call_args[1] == "assistant"
    assert call_args[2] == "你"
    assert call_kwargs["completion_status"] == COMPLETION_INTERRUPTED
    db.commit.assert_awaited()
    service.conversations.invalidate_list_cache.assert_awaited_with(user_id)


@pytest.mark.asyncio
async def test_iter_tokens_survives_disconnect_poll_timeouts():
    service = ChatService(AsyncMock(), redis=None, runner=MagicMock())

    async def slow_stream(*_args, **_kwargs):
        await asyncio.sleep(0.35)
        yield "你"
        await asyncio.sleep(0.35)
        yield "好"

    service.runner.stream_tokens = slow_stream

    tokens: list[str] = []
    async for token in service._iter_tokens_with_disconnect(
        MagicMock(),
        conversation_id=uuid.uuid4(),
        request=None,
    ):
        tokens.append(token)

    assert tokens == ["你", "好"]
