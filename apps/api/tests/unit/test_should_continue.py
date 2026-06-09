"""should_continue routing: ReAct loop vs END (EP05)."""

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END

from app.graphs.nodes.execute_tools import should_continue


def test_should_continue_end_on_empty_messages():
    assert should_continue({"messages": [], "user_id": "u1"}) is END


def test_should_continue_end_when_last_is_human():
    state = {
        "messages": [HumanMessage(content="hi")],
        "user_id": "u1",
    }
    assert should_continue(state) is END


def test_should_continue_end_when_last_is_tool_message():
    state = {
        "messages": [
            AIMessage(content="", tool_calls=[{"id": "c1", "name": "x", "args": {}}]),
            ToolMessage(content='{"success": false}', tool_call_id="c1", name="x"),
        ],
        "user_id": "u1",
    }
    assert should_continue(state) is END


def test_should_continue_routes_to_execute_tools_when_tool_calls_present():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"id": "call_1", "name": "tavily_search", "args": {"query": "x"}}],
            )
        ],
        "user_id": "u1",
    }
    assert should_continue(state) == "execute_tools"


def test_should_continue_end_when_assistant_has_no_tool_calls():
    state = {
        "messages": [AIMessage(content="done")],
        "user_id": "u1",
    }
    assert should_continue(state) is END


def test_should_continue_end_when_tool_calls_list_empty():
    state = {
        "messages": [AIMessage(content="", tool_calls=[])],
        "user_id": "u1",
    }
    assert should_continue(state) is END
