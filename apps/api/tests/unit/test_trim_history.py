"""trim_history graph node (EP06 short-term memory)."""

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from app.core.config import settings
from app.graphs.nodes.trim_history import trim_history


def _unwrap_messages(payload: list) -> list:
    return [message for message in payload if not isinstance(message, RemoveMessage)]


@pytest.mark.asyncio
async def test_trim_history_skipped_when_memory_disabled(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", False)
    state = {
        "messages": [HumanMessage(content="hello")],
        "user_id": "u1",
    }
    result = await trim_history(state)
    assert result["trim_stats"]["skipped"] is True
    assert result["trim_stats"]["reason"] == "memory_disabled"


@pytest.mark.asyncio
async def test_trim_history_skipped_when_short_term_disabled(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", False)
    state = {
        "messages": [HumanMessage(content="hello")],
        "user_id": "u1",
    }
    result = await trim_history(state)
    assert result["trim_stats"]["skipped"] is True
    assert result["trim_stats"]["reason"] == "memory_short_term_disabled"


@pytest.mark.asyncio
async def test_trim_history_keeps_short_history(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好！"),
    ]
    state = {"messages": messages, "user_id": "u1"}
    result = await trim_history(state)
    assert "messages" not in result
    assert result["trim_stats"]["dropped_turns"] == 0
    assert result["trim_stats"]["trimmed"] is False


@pytest.mark.asyncio
async def test_trim_history_drops_old_turns(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)
    monkeypatch.setattr(settings, "max_context_tokens", 500)
    monkeypatch.setattr(settings, "reserve_for_reply", 100)

    messages: list = []
    for index in range(10):
        messages.append(HumanMessage(content=f"user-{index}-" + ("x" * 200)))
        messages.append(AIMessage(content=f"assistant-{index}-" + ("y" * 200)))

    state = {"messages": messages, "user_id": "u1"}
    result = await trim_history(state)

    assert result["trim_stats"]["trimmed"] is True
    assert result["trim_stats"]["dropped_turns"] > 0
    trimmed = _unwrap_messages(result["messages"])
    assert len(trimmed) < len(messages)
    assert trimmed[-2].content.startswith("user-9-")


@pytest.mark.asyncio
async def test_trim_history_reserves_context_summary(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)

    short_messages = [HumanMessage(content="hi"), AIMessage(content="ok")]
    without_summary = await trim_history(
        {"messages": short_messages, "user_id": "u1"}
    )
    with_summary = await trim_history(
        {
            "messages": short_messages,
            "user_id": "u1",
            "context_summary": "用户偏好简洁回答。" + ("z" * 400),
        }
    )

    assert without_summary["trim_stats"]["reserved_prompt_tokens"] == 0
    assert with_summary["trim_stats"]["reserved_prompt_tokens"] > 100


@pytest.mark.asyncio
async def test_trim_history_reserves_memory_snippets(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)

    short_messages = [HumanMessage(content="hi"), AIMessage(content="ok")]
    without_snippets = await trim_history(
        {"messages": short_messages, "user_id": "u1"}
    )
    with_snippets = await trim_history(
        {
            "messages": short_messages,
            "user_id": "u1",
            "memory_snippets": [
                {"type": "preference", "content": "喜欢简洁回答。" + ("x" * 300)},
            ],
        }
    )

    assert with_snippets["trim_stats"]["reserved_prompt_tokens"] > without_snippets[
        "trim_stats"
    ]["reserved_prompt_tokens"]


@pytest.mark.asyncio
async def test_trim_history_summary_reduces_kept_turns(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)
    monkeypatch.setattr(settings, "max_context_tokens", 400)
    monkeypatch.setattr(settings, "reserve_for_reply", 80)

    messages: list = []
    for index in range(8):
        messages.append(HumanMessage(content=f"u{index}-" + ("a" * 100)))
        messages.append(AIMessage(content=f"a{index}-" + ("b" * 100)))

    without_summary = await trim_history({"messages": messages, "user_id": "u1"})
    with_summary = await trim_history(
        {
            "messages": messages,
            "user_id": "u1",
            "context_summary": "用户偏好简洁回答。" + ("z" * 350),
        }
    )

    assert "messages" in without_summary
    assert "messages" in with_summary
    loose_trimmed = _unwrap_messages(without_summary["messages"])
    tight_trimmed = _unwrap_messages(with_summary["messages"])
    assert len(tight_trimmed) < len(loose_trimmed)


@pytest.mark.asyncio
async def test_trim_history_rag_reserve_includes_top_k_buffer(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_short_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_top_k", 5)

    result = await trim_history(
        {
            "messages": [HumanMessage(content="hi"), AIMessage(content="ok")],
            "user_id": "u1",
        }
    )

    assert result["trim_stats"]["reserved_prompt_tokens"] >= 5 * 256
