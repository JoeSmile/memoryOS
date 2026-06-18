"""ChatService context_summary graph state and detached background scheduling."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.models import Conversation, Message
from app.models.message import COMPLETION_INTERRUPTED
from app.services import chat_service
from app.services.chat_service import ChatService, CompletionStreamState
from app.services.memory.long_term import run_extract_background
from app.services.memory.summary_service import run_summary_background


@pytest.fixture
def capture_detached_background(monkeypatch):
    scheduled: list[tuple[str, object]] = []

    def _fake_schedule(coro, *, name: str) -> None:
        scheduled.append((name, coro))
        coro.close()

    monkeypatch.setattr(chat_service, "_schedule_detached_background", _fake_schedule)
    return scheduled


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


def _message(role: str, content: str) -> Message:
    now = datetime.now(timezone.utc)
    return Message(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        role=role,
        content=content,
        created_at=now,
    )


def test_to_graph_state_includes_context_summary():
    user_id = uuid.uuid4()
    history = [_message("user", "hi")]

    state = ChatService._to_graph_state(
        user_id,
        history,
        context_summary="用户偏好简洁",
    )

    assert state["context_summary"] == "用户偏好简洁"
    assert state["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_stream_completion_events_passes_context_summary_to_graph():
    db = AsyncMock()
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="t",
        context_summary="已有会话摘要",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user_row = _message("user", "question")
    captured_state: dict = {}

    async def spy_stream_events(state, **kwargs):
        captured_state["state"] = state
        return
        yield  # pragma: no cover

    runner = MagicMock()
    runner.stream_events = spy_stream_events
    runner.last_retrieved_chunks = []

    service = ChatService(db, redis=None, runner=runner)
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.conversations.get_owned_conversation = AsyncMock(return_value=conversation)
    service.cancel_cache.register_active = AsyncMock()
    service.cancel_cache.is_cancelled = AsyncMock(return_value=False)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    stream_state = CompletionStreamState(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    async for _ in service.stream_completion_events(stream_state=stream_state):
        pass

    assert captured_state["state"]["context_summary"] == "已有会话摘要"


@pytest.mark.asyncio
async def test_finalize_schedules_summary_background_task_when_triggered(
    monkeypatch,
    capture_detached_background,
):
    monkeypatch.setattr(settings, "summary_trigger_tokens", 512)
    db = AsyncMock()
    db.commit = AsyncMock()
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="t",
        created_at=now,
        updated_at=now,
    )
    messages = [
        Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="u-" + ("x" * 2000),
            created_at=now,
        ),
        Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content="a-" + ("y" * 2000),
            created_at=now,
        ),
    ]
    assistant_row = MagicMock()
    assistant_row.id = uuid.uuid4()
    assistant_row.metadata_ = None

    service = ChatService(db, redis=None, runner=MagicMock())
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.messages.list_by_conversation_id = AsyncMock(return_value=messages)
    service.conversations.conversations.get_by_id = AsyncMock(return_value=conversation)
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=None)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    stream_state = CompletionStreamState(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    stream_state.assistant_parts = ["reply"]
    stream_state.stream_exhausted = True

    await service.finalize_completion_stream(stream_state)

    assert len(capture_detached_background) == 2
    extract_name, extract_coro = capture_detached_background[0]
    summary_name, summary_coro = capture_detached_background[1]
    assert extract_name == f"memory-extract-{conversation_id}"
    assert extract_coro.cr_code.co_name == run_extract_background.__name__
    assert summary_name == f"summary-{conversation_id}"
    assert summary_coro.cr_code.co_name == run_summary_background.__name__


@pytest.mark.asyncio
async def test_finalize_skips_summary_schedule_when_below_threshold(
    capture_detached_background,
):
    db = AsyncMock()
    db.commit = AsyncMock()
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="t",
        created_at=now,
        updated_at=now,
    )
    messages = [
        Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="短",
            created_at=now,
        ),
    ]
    assistant_row = MagicMock()
    assistant_row.id = uuid.uuid4()

    service = ChatService(db, redis=None, runner=MagicMock())
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.messages.list_by_conversation_id = AsyncMock(return_value=messages)
    service.conversations.conversations.get_by_id = AsyncMock(return_value=conversation)
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=None)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    stream_state = CompletionStreamState(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    stream_state.assistant_parts = ["ok"]
    stream_state.stream_exhausted = True

    await service.finalize_completion_stream(stream_state)

    assert len(capture_detached_background) == 1
    name, coro = capture_detached_background[0]
    assert name == f"memory-extract-{conversation_id}"
    assert coro.cr_code.co_name == run_extract_background.__name__


@pytest.mark.asyncio
async def test_finalize_skips_extract_when_long_term_disabled(
    monkeypatch,
    capture_detached_background,
):
    monkeypatch.setattr(settings, "memory_long_term_enabled", False)
    monkeypatch.setattr(settings, "summary_trigger_tokens", 512)

    db = AsyncMock()
    db.commit = AsyncMock()
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="t",
        created_at=now,
        updated_at=now,
    )
    messages = [
        Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="u-" + ("x" * 2000),
            created_at=now,
        ),
        Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content="a-" + ("y" * 2000),
            created_at=now,
        ),
    ]
    assistant_row = MagicMock()
    assistant_row.id = uuid.uuid4()

    service = ChatService(db, redis=None, runner=MagicMock())
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.messages.list_by_conversation_id = AsyncMock(return_value=messages)
    service.conversations.conversations.get_by_id = AsyncMock(return_value=conversation)
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=None)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    stream_state = CompletionStreamState(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    stream_state.assistant_parts = ["reply"]
    stream_state.stream_exhausted = True

    await service.finalize_completion_stream(stream_state)

    assert len(capture_detached_background) == 1
    name, coro = capture_detached_background[0]
    assert name == f"summary-{conversation_id}"
    assert coro.cr_code.co_name == run_summary_background.__name__


@pytest.mark.asyncio
async def test_finalize_skips_summary_schedule_when_interrupted(
    capture_detached_background,
):
    db = AsyncMock()
    db.commit = AsyncMock()
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    assistant_row = MagicMock()
    assistant_row.id = uuid.uuid4()

    service = ChatService(db, redis=None, runner=MagicMock())
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=None)
    service.cancel_cache.clear = AsyncMock()
    service.stream_cache.delete = AsyncMock()

    stream_state = CompletionStreamState(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    stream_state.assistant_parts = ["partial"]
    stream_state.disconnected = True

    await service.finalize_completion_stream(stream_state)

    assert capture_detached_background == []
    create_kwargs = service.messages.create.await_args.kwargs
    assert create_kwargs["completion_status"] == COMPLETION_INTERRUPTED
