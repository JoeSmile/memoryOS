"""ChatGraphRunner ReAct stream events (tool_call / tool_result / token)."""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes.mock_model import MOCK_AFTER_TOOL_CHUNKS, MOCK_TOKEN_CHUNKS
from app.graphs.runner import ChatGraphRunner


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.fixture(autouse=True)
def fresh_chat_graph():
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


def _sample_chunk() -> dict:
    return {
        "external_id": "wc-1",
        "collection": "samples",
        "score": 0.9,
        "content": "fact",
        "document_id": str(uuid4()),
        "entity_type": "fact_card",
    }


@pytest.mark.asyncio
async def test_stream_events_weak_rag_emits_tool_pair_then_tokens():
    runner = ChatGraphRunner()
    events: list[dict] = []
    async for event in runner.stream_events(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "u1",
            "retrieved_chunks": [],
            "rag_sufficient": False,
        },
        thread_id="conv-1",
    ):
        events.append(event)

    types = [event["type"] for event in events]
    assert types == ["tool_call", "tool_result", "token", "token", "token", "token"]
    assert events[0]["data"]["name"] == "tavily_search"
    assert events[1]["data"]["name"] == "tavily_search"
    assert events[1]["data"]["success"] is True
    assert [event["content"] for event in events if event["type"] == "token"] == (
        MOCK_AFTER_TOOL_CHUNKS
    )


@pytest.mark.asyncio
async def test_stream_events_sufficient_rag_tokens_only():
    runner = ChatGraphRunner()
    events: list[dict] = []
    async for event in runner.stream_events(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "u1",
            "retrieved_chunks": [_sample_chunk()],
            "rag_sufficient": True,
        },
        thread_id="conv-1",
    ):
        events.append(event)

    assert all(event["type"] == "token" for event in events)
    assert [event["content"] for event in events] == MOCK_TOKEN_CHUNKS


@pytest.mark.asyncio
async def test_stream_tokens_delegates_to_token_events():
    runner = ChatGraphRunner()
    tokens: list[str] = []
    async for token in runner.stream_tokens(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "u1",
            "retrieved_chunks": [_sample_chunk()],
            "rag_sufficient": True,
        },
        thread_id="conv-1",
    ):
        tokens.append(token)
    assert tokens == MOCK_TOKEN_CHUNKS
