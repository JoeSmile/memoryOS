"""Chat graph invoke + mock streaming (no network)."""

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes.mock_model import MOCK_ASSISTANT_TEXT, MOCK_TOKEN_CHUNKS
from app.graphs.runner import ChatGraphRunner


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.mark.asyncio
async def test_chat_graph_invoke_mock():
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="hi")],
            "user_id": "test-user",
        }
    )
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
