"""ChatService SSE tool_call / tool_result + metadata.tool_steps."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes.mock_model import (
    MOCK_AFTER_TOOL_TEXT,
    MOCK_ASSISTANT_TEXT,
    MOCK_TOKEN_CHUNKS,
)
from app.graphs.runner import ChatGraphRunner
from app.models.message import COMPLETION_COMPLETE
from app.services.chat_service import ChatService


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.fixture(autouse=True)
def fresh_chat_graph():
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


def _service_with_mocks() -> tuple[ChatService, MagicMock, uuid.UUID, uuid.UUID]:
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
    assistant_row.content = MOCK_AFTER_TOOL_TEXT
    assistant_row.completion_status = COMPLETION_COMPLETE
    assistant_row.metadata_ = None

    service = ChatService(db, redis=None, runner=ChatGraphRunner())
    service.messages.list_by_conversation_id = AsyncMock(return_value=[user_row])
    service.messages.create = AsyncMock(return_value=assistant_row)
    service.stream_cache.append = AsyncMock()
    service.stream_cache.delete = AsyncMock()
    service.cancel_cache.register_active = AsyncMock()
    service.cancel_cache.is_cancelled = AsyncMock(return_value=False)
    service.cancel_cache.get_visible_content = AsyncMock(return_value=None)
    service.cancel_cache.get_visible_length = AsyncMock(return_value=None)
    service.cancel_cache.clear = AsyncMock()
    service.conversations.touch_activity = AsyncMock()
    service.conversations.invalidate_list_cache = AsyncMock()

    return service, assistant_row, conversation_id, user_id


@pytest.mark.asyncio
async def test_stream_completion_events_weak_rag_tool_sse_order():
    service, _, conversation_id, user_id = _service_with_mocks()
    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    events: list[dict] = []
    async for event in service.stream_completion_events(stream_state=stream_state):
        events.append(event)

    names = [event["event"] for event in events]
    assert names[0] == "start"
    assert names[1:3] == ["tool_call", "tool_result"]
    assert all(name == "token" for name in names[3:])
    assert stream_state.tool_steps
    assert stream_state.tool_steps[0]["name"] == "tavily_search"
    assert stream_state.tool_steps[0]["success"] is True


@pytest.mark.asyncio
async def test_stream_completion_events_sufficient_rag_no_tool_sse():
    service, _, conversation_id, user_id = _service_with_mocks()

    async def token_only_stream(_state, **kwargs):
        for chunk in MOCK_TOKEN_CHUNKS:
            yield {"type": "token", "content": chunk}

    service.runner.stream_events = token_only_stream  # type: ignore[method-assign]

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    events: list[dict] = []
    async for event in service.stream_completion_events(stream_state=stream_state):
        events.append(event)

    names = [event["event"] for event in events]
    assert "tool_call" not in names
    assert "tool_result" not in names
    assert names.count("token") == 3
    assert stream_state.tool_steps == []


@pytest.mark.asyncio
async def test_finalize_persists_tool_steps_metadata():
    service, assistant_row, conversation_id, user_id = _service_with_mocks()
    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    async for _event in service.stream_completion_events(stream_state=stream_state):
        pass

    await service.finalize_completion_stream(stream_state)

    metadata = assistant_row.metadata_
    assert metadata is not None
    assert "tool_steps" in metadata
    assert metadata["tool_steps"][0]["name"] == "tavily_search"
    assert metadata["tool_steps"][0]["summary"]


@pytest.mark.asyncio
async def test_finalize_persists_tool_steps_when_stopped_before_tokens():
    service, assistant_row, conversation_id, user_id = _service_with_mocks()
    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    stream_state.tool_steps = [
        {
            "id": "mock_call_tavily",
            "name": "tavily_search",
            "arguments": {"query": "mock web search"},
            "success": True,
            "summary": "mock summary",
        }
    ]
    stream_state.disconnected = True

    await service.finalize_completion_stream(stream_state)

    service.messages.create.assert_called_once()
    assert service.messages.create.call_args[0][2] == ""
    assert assistant_row.metadata_["tool_steps"] == stream_state.tool_steps


@pytest.mark.asyncio
async def test_stream_completion_events_ignores_unknown_runner_event():
    service, _, conversation_id, user_id = _service_with_mocks()

    async def mixed_stream(_state, **kwargs):
        yield {"type": "tool_call", "data": {"id": "c1", "name": "x", "arguments": {}}}
        yield {"type": "weird", "data": {}}
        yield {
            "type": "tool_result",
            "data": {"id": "c1", "name": "x", "success": False, "summary": "err"},
        }
        for chunk in MOCK_TOKEN_CHUNKS:
            yield {"type": "token", "content": chunk}

    service.runner.stream_events = mixed_stream  # type: ignore[method-assign]

    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    events: list[dict] = []
    async for event in service.stream_completion_events(stream_state=stream_state):
        events.append(event)

    names = [event["event"] for event in events]
    assert "weird" not in names
    assert names.count("token") == 3
    assert len(stream_state.tool_steps) == 1


@pytest.mark.asyncio
async def test_agent_tools_disabled_skips_tool_sse(monkeypatch):
    monkeypatch.setattr(settings, "agent_tools_enabled", False)

    service, _, conversation_id, user_id = _service_with_mocks()
    stream_state = service.new_completion_stream_state(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    events: list[dict] = []
    async for event in service.stream_completion_events(stream_state=stream_state):
        events.append(event)

    names = [event["event"] for event in events]
    assert "tool_call" not in names
    assert "tool_result" not in names
    assert names.count("token") == 3
    assert "".join(stream_state.assistant_parts) == MOCK_ASSISTANT_TEXT
