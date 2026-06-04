"""Minimal graph wiring tests (mock path, no network)."""

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph


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
    assert result["messages"]
    last = result["messages"][-1]
    assert last.content == "你好！"
