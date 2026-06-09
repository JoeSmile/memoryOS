"""Chat graph invoke + mock streaming (no network)."""

from uuid import uuid4

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from langchain_core.messages import HumanMessage, ToolMessage

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes.mock_model import (
    MOCK_AFTER_TOOL_TEXT,
    MOCK_ASSISTANT_TEXT,
    MOCK_TOKEN_CHUNKS,
)
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
async def test_chat_graph_invoke_mock_weak_rag_react():
    """No qualifying RAG → mock requests tavily_search then answers."""
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "test-user",
            "retrieved_chunks": [],
            "rag_sufficient": False,
        }
    )
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "tavily_search"
    assert result["messages"][-1].content == MOCK_AFTER_TOOL_TEXT


@pytest.mark.asyncio
async def test_chat_graph_invoke_mock_sufficient_rag_no_tools():
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "test-user",
            "retrieved_chunks": [_sample_chunk()],
            "rag_sufficient": True,
        }
    )
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert tool_messages == []
    assert result["messages"][-1].content == MOCK_ASSISTANT_TEXT


@pytest.mark.asyncio
async def test_stream_tokens_mock():
    runner = ChatGraphRunner()
    tokens: list[str] = []
    async for token in runner.stream_tokens(
        {"messages": [HumanMessage(content="hi")], "user_id": "u1"},
        thread_id="conv-1",
    ):
        tokens.append(token)
    assert tokens == MOCK_TOKEN_CHUNKS
    assert "".join(tokens) == MOCK_ASSISTANT_TEXT
