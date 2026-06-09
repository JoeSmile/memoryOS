"""execute_tools node: ToolMessage contract and malformed call handling."""

import json

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage

from app.graphs.nodes.execute_tools import execute_tools


@pytest.mark.asyncio
async def test_execute_tools_replies_for_malformed_tool_call():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_bad", "name": "", "args": {}},
                ],
            )
        ],
        "user_id": "user-1",
    }
    update = await execute_tools(state, {})
    messages = update["messages"]
    assert len(messages) == 1
    assert messages[0].tool_call_id == "call_bad"
    payload = json.loads(messages[0].content)
    assert payload["success"] is False
    assert "malformed_tool_call" in payload["error"]


@pytest.mark.asyncio
async def test_execute_tools_assigns_placeholder_id_when_missing():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "", "name": "", "args": {}},
                ],
            )
        ],
        "user_id": "user-1",
    }
    update = await execute_tools(state, {})
    assert update["messages"][0].tool_call_id == "malformed_0"


@pytest.mark.asyncio
async def test_execute_tools_runs_registered_tool(monkeypatch):
    monkeypatch.setattr(
        "app.tools.builtin.tavily_search.settings.tavily_api_key",
        None,
    )
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_ok",
                        "name": "tavily_search",
                        "args": {"query": "memoryOS"},
                    }
                ],
            )
        ],
        "user_id": "user-1",
    }
    update = await execute_tools(state, {})
    messages = update["messages"]
    assert len(messages) == 1
    assert messages[0].name == "tavily_search"
    payload = json.loads(messages[0].content)
    assert payload["success"] is True
    assert payload["summary"]
