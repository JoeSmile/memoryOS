"""L1 Harness：Unified ReAct SSE + metadata.tool_steps（mock LLM + mock Tavily）。"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes.mock_model import MOCK_AFTER_TOOL_TEXT, MOCK_ASSISTANT_TEXT
from app.main import app
from tests.harness.test_rag_chat_contract import (
    NO_HIT_QUERY,
    _create_conversation,
    _event_index,
    _list_conversation_messages,
    _register_and_login,
    _stream_chat_events,
)
from tests.harness.test_rag_contract import SEEDED_QUERY, _ingest_samples


@pytest.fixture(autouse=True)
def _unified_react_harness(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "tavily_api_key", None)
    monkeypatch.setattr(settings, "rag_chat_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_top_k", 5)
    monkeypatch.setattr(settings, "rag_chat_min_score", 0.35)
    monkeypatch.setattr(settings, "rag_chat_collection", None)
    monkeypatch.setattr(settings, "agent_tools_enabled", True)
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


@pytest.fixture(autouse=True)
def _clear_worldcup_ingest_locks():
    from app.cache import ingest_lock
    from app.cache.keys import worldcup_ingest_stem_lock_key
    from app.services.knowledge_ingest_service import DEFAULT_COLLECTION_STEMS

    def _clear() -> None:
        ingest_lock._LOCAL_KEYS.clear()
        if not settings.redis_url:
            return
        import redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            keys = [
                worldcup_ingest_stem_lock_key(stem) for stem in DEFAULT_COLLECTION_STEMS
            ]
            client.delete(*keys)
        finally:
            client.close()

    _clear()
    yield
    _clear()


@pytest.mark.asyncio
async def test_unified_react_sufficient_rag_no_tool_events():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        await _ingest_samples(client, headers)

        conversation_id = await _create_conversation(
            client,
            token,
            user_id,
            title="Harness unified sufficient",
        )
        events = await _stream_chat_events(
            client,
            token=token,
            conversation_id=conversation_id,
            content=SEEDED_QUERY,
        )

        assert _event_index(events, "tool_call") == -1
        assert _event_index(events, "tool_result") == -1

        sources_index = _event_index(events, "sources")
        token_index = _event_index(events, "token")
        assert sources_index >= 0
        assert token_index >= 0
        assert sources_index < token_index

        token_events = [event for event in events if event.get("event") == "token"]
        assert "".join(event["data"]["content"] for event in token_events) == (
            MOCK_ASSISTANT_TEXT
        )

        done_index = _event_index(events, "done")
        assert done_index >= 0
        message_id = events[done_index]["data"]["message_id"]

        rows = await _list_conversation_messages(
            client,
            token=token,
            conversation_id=conversation_id,
        )
        assistant = next(row for row in rows if row["id"] == message_id)
        metadata = assistant.get("metadata")
        assert metadata is not None
        assert metadata.get("rag_sources")
        assert "tool_steps" not in metadata


@pytest.mark.asyncio
async def test_unified_react_weak_rag_emits_tool_sse_and_persists_tool_steps():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conversation_id = await _create_conversation(
            client,
            token,
            user_id,
            title="Harness unified weak",
        )
        events = await _stream_chat_events(
            client,
            token=token,
            conversation_id=conversation_id,
            content=NO_HIT_QUERY,
        )

        tool_call_index = _event_index(events, "tool_call")
        tool_result_index = _event_index(events, "tool_result")
        token_index = _event_index(events, "token")
        done_index = _event_index(events, "done")

        assert tool_call_index >= 0
        assert tool_result_index >= 0
        assert token_index >= 0
        assert done_index >= 0
        assert tool_call_index < tool_result_index < token_index

        tool_call = events[tool_call_index]
        assert tool_call["data"]["name"] == "tavily_search"
        assert tool_call["data"]["arguments"]["query"]

        tool_result = events[tool_result_index]
        assert tool_result["data"]["name"] == "tavily_search"
        assert tool_result["data"]["success"] is True
        assert tool_result["data"]["summary"]

        token_events = [event for event in events if event.get("event") == "token"]
        assert "".join(event["data"]["content"] for event in token_events) == (
            MOCK_AFTER_TOOL_TEXT
        )

        message_id = events[done_index]["data"]["message_id"]
        rows = await _list_conversation_messages(
            client,
            token=token,
            conversation_id=conversation_id,
        )
        assistant = next(row for row in rows if row["id"] == message_id)
        assert assistant["content"] == MOCK_AFTER_TOOL_TEXT

        metadata = assistant.get("metadata")
        assert metadata is not None
        tool_steps = metadata.get("tool_steps")
        assert isinstance(tool_steps, list)
        assert len(tool_steps) >= 1
        step = tool_steps[0]
        assert step["name"] == "tavily_search"
        assert step["success"] is True
        assert step["arguments"]["query"]
        assert step["summary"]
