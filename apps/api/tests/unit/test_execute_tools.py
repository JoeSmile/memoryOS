"""execute_tools node: ToolMessage contract and malformed call handling."""

import json

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage, ToolMessage

from app.graphs.nodes.execute_tools import execute_tools, should_continue


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


def test_should_continue_ends_when_last_message_is_tool_message():
    state = {
        "messages": [
            AIMessage(content="", tool_calls=[{"id": "c1", "name": "x", "args": {}}]),
            ToolMessage(content='{"success": false}', tool_call_id="c1", name="x"),
        ],
        "user_id": "user-1",
    }
    from langgraph.graph import END

    assert should_continue(state) is END
