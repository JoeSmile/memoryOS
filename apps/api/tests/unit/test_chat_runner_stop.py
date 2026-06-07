"""ChatGraphRunner stops on cancel flag or slow-stream poll."""

import asyncio
import uuid

import pytest

from app.cache.stream_cancel_cache import StreamCancelCache
from app.core.config import settings
from app.graphs.nodes.mock_model import MOCK_TOKEN_CHUNKS
from app.graphs.runner import ChatGraphRunner


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.mark.asyncio
async def test_runner_stops_when_cancel_flag_set(monkeypatch):
    from app.graphs.nodes import mock_model

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow():
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

    cache = StreamCancelCache(redis=None)
    stream_id = str(uuid.uuid4())
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await cache.register_active(stream_id, conversation_id, user_id)

    runner = ChatGraphRunner()
    state = {"messages": [], "user_id": str(user_id)}

    async def cancel_after_delay() -> None:
        await asyncio.sleep(0.45)
        await cache.set_cancelled(stream_id)

    cancel_task = asyncio.create_task(cancel_after_delay())
    tokens: list[str] = []
    try:
        async for token in runner.stream_tokens(
            state,
            thread_id=str(conversation_id),
            stream_id=stream_id,
            cancel_cache=cache,
        ):
            tokens.append(token)
    finally:
        await cancel_task

    assert tokens
    assert len(tokens) < len(MOCK_TOKEN_CHUNKS)
    await cache.clear(stream_id)


@pytest.mark.asyncio
async def test_runner_survives_slow_stream_poll_timeouts(monkeypatch):
    from app.graphs.nodes import mock_model

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow():
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)

    runner = ChatGraphRunner()
    tokens: list[str] = []
    async for token in runner.stream_tokens(
        {"messages": [], "user_id": "u1"},
        thread_id="conv-1",
    ):
        tokens.append(token)

    assert tokens == MOCK_TOKEN_CHUNKS
