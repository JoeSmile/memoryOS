"""ChatService interrupted assistant persistence."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.graphs.runner import ChatGraphRunner
from app.models.message import COMPLETION_INTERRUPTED
from app.services.chat_service import ChatService


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


class _DisconnectAfterFirstToken:
    def __init__(self) -> None:
        self._calls = 0

    async def is_disconnected(self) -> bool:
        self._calls += 1
        # Allow first slow token (0.35s) before disconnect on subsequent polls.
        return self._calls > 2


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

    service = ChatService(db, redis=None, runner=ChatGraphRunner())

    service.conversations.get_owned_conversation = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()
    service.cancel_cache.register_active = AsyncMock()
    service.cancel_cache.clear = AsyncMock()

    from app.graphs.nodes import mock_model

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow(delay_seconds=0.35):
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

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

    assert len(events) == 2
    assert events[0]["event"] == "start"
    assert events[1]["event"] == "token"
    assert events[1]["data"]["content"] == "你"
    service.messages.create.assert_called_once()
    call_args, call_kwargs = service.messages.create.call_args
    assert call_args[1] == "assistant"
    assert call_args[2] == "你"
    assert call_kwargs["completion_status"] == COMPLETION_INTERRUPTED
    db.commit.assert_awaited()
    service.conversations.invalidate_list_cache.assert_awaited_with(user_id)


@pytest.mark.asyncio
async def test_iter_tokens_delegates_stream_id_to_runner():
    service = ChatService(AsyncMock(), redis=None, runner=MagicMock())

    captured: dict = {}

    async def fake_stream(*_args, **kwargs):
        captured.update(kwargs)
        yield "你"

    service.runner.stream_tokens = fake_stream

    tokens: list[str] = []
    stream_id = str(uuid.uuid4())
    async for token in service._iter_tokens_with_disconnect(
        MagicMock(),
        conversation_id=uuid.uuid4(),
        stream_id=stream_id,
        request=None,
    ):
        tokens.append(token)

    assert tokens == ["你"]
    assert captured["stream_id"] == stream_id
    assert captured["cancel_cache"] is service.cancel_cache


@pytest.mark.asyncio
async def test_stream_stops_when_cancelled_mid_stream(monkeypatch):
    from app.graphs.nodes import mock_model

    db = AsyncMock()
    db.commit = AsyncMock()

    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    user_row = MagicMock()
    user_row.id = uuid.uuid4()
    user_row.role = "user"
    user_row.content = "hi"

    service = ChatService(db, redis=None, runner=ChatGraphRunner())
    service.conversations.get_owned_conversation = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock()
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow():
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    events: list[dict] = []
    async for event in service.stream_completion_events(stream_state=stream_state):
        events.append(event)
        if event.get("event") == "start":
            await service.cancel_stream(
                stream_id=stream_state.stream_id,
                user_id=user_id,
            )

    token_events = [event for event in events if event.get("event") == "token"]
    assert events[0]["event"] == "start"
    assert len(token_events) < len(mock_model.MOCK_TOKEN_CHUNKS)

    await service.finalize_completion_stream(stream_state)
    if token_events:
        service.messages.create.assert_called_once()
        assert (
            service.messages.create.call_args[1]["completion_status"]
            == COMPLETION_INTERRUPTED
        )


@pytest.mark.asyncio
async def test_stream_persists_interrupted_assistant_on_cancel(monkeypatch):
    from app.graphs.nodes import mock_model

    db = AsyncMock()
    db.commit = AsyncMock()

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

    service = ChatService(db, redis=None, runner=ChatGraphRunner())
    service.conversations.get_owned_conversation = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow(delay_seconds=0.35):
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    async def cancel_after_start() -> None:
        import asyncio

        await asyncio.sleep(0.45)
        await service.cancel_stream(
            stream_id=stream_state.stream_id,
            user_id=user_id,
        )

    import asyncio

    cancel_task = asyncio.create_task(cancel_after_start())
    events: list[dict] = []
    try:
        async for event in service.stream_completion_events(
            stream_state=stream_state,
        ):
            events.append(event)
    finally:
        await cancel_task

    await service.finalize_completion_stream(stream_state)

    token_events = [event for event in events if event.get("event") == "token"]
    assert token_events
    assert len(token_events) < len(mock_model.MOCK_TOKEN_CHUNKS)
    service.messages.create.assert_called_once()
    call_kwargs = service.messages.create.call_args[1]
    assert call_kwargs["completion_status"] == COMPLETION_INTERRUPTED
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_finalize_truncates_to_visible_content_on_cancel(monkeypatch):
    from app.graphs.nodes import mock_model

    db = AsyncMock()
    db.commit = AsyncMock()

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

    service = ChatService(db, redis=None, runner=ChatGraphRunner())
    service.conversations.get_owned_conversation = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow(delay_seconds=0.35):
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    import asyncio

    async def cancel_with_visible() -> None:
        await asyncio.sleep(0.45)
        await service.cancel_stream(
            stream_id=stream_state.stream_id,
            user_id=user_id,
            visible_content="你",
        )

    cancel_task = asyncio.create_task(cancel_with_visible())
    try:
        async for _event in service.stream_completion_events(
            stream_state=stream_state,
        ):
            pass
    finally:
        await cancel_task

    await service.finalize_completion_stream(stream_state)

    service.messages.create.assert_called_once()
    assert service.messages.create.call_args[0][2] == "你"


@pytest.mark.asyncio
async def test_finalize_skips_empty_content_when_visible_length_zero():
    db = AsyncMock()
    service = ChatService(db, redis=None)
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=0)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()
    service.messages.create = AsyncMock()

    stream_state = service.new_completion_stream_state(
        conversation_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    stream_state.assistant_parts = ["你"]

    result = await service.finalize_completion_stream(stream_state)

    assert result is None
    service.messages.create.assert_not_awaited()
