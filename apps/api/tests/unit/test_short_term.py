from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.services.memory.short_term import (
    prompt_token_budget,
    trim_messages,
)


def test_trim_empty():
    result = trim_messages(
        [],
        model="qwen-turbo",
        max_context_tokens=8192,
        reserve_for_reply=1024,
    )
    assert result.messages == []
    assert result.dropped_turns == 0
    assert result.token_count == 0


def test_trim_under_budget_unchanged():
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好！"),
    ]
    result = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=8192,
        reserve_for_reply=1024,
    )
    assert result.messages == messages
    assert result.dropped_turns == 0


def test_prompt_token_budget_clamps_when_reserve_too_large():
    assert prompt_token_budget(
        max_context_tokens=8192,
        reserve_for_reply=1024,
    ) == 7168
    assert prompt_token_budget(
        max_context_tokens=1000,
        reserve_for_reply=900,
    ) == 256


def test_trim_drops_oldest_turns_keeps_latest():
    messages: list = []
    for index in range(10):
        messages.append(HumanMessage(content=f"user-{index}-" + ("x" * 200)))
        messages.append(AIMessage(content=f"assistant-{index}-" + ("y" * 200)))

    result = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=500,
        reserve_for_reply=100,
    )

    assert len(result.messages) < len(messages)
    assert result.dropped_turns > 0
    assert result.messages[-2].content.startswith("user-9-")
    assert result.token_count <= prompt_token_budget(
        max_context_tokens=500,
        reserve_for_reply=100,
    )


def test_reserved_prompt_tokens_reduces_history_kept():
    messages: list = []
    for index in range(6):
        messages.append(HumanMessage(content=f"u{index}-" + ("a" * 120)))
        messages.append(AIMessage(content=f"a{index}-" + ("b" * 120)))

    loose = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=900,
        reserve_for_reply=100,
        reserved_prompt_tokens=0,
    )
    tight = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=900,
        reserve_for_reply=100,
        reserved_prompt_tokens=350,
    )

    assert len(tight.messages) <= len(loose.messages)


def test_trim_keeps_react_tool_round_with_last_human():
    messages = [
        HumanMessage(content="old-" + ("x" * 2000)),
        AIMessage(content="old-reply-" + ("y" * 2000)),
        HumanMessage(content="search"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "tavily_search",
                    "args": {"query": "q"},
                    "id": "call_1",
                }
            ],
        ),
        ToolMessage(
            content='{"results":[]}',
            tool_call_id="call_1",
            name="tavily_search",
        ),
        AIMessage(content="final answer"),
    ]

    result = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=280,
        reserve_for_reply=80,
    )

    assert result.messages[0].content == "search"
    assert any(isinstance(message, ToolMessage) for message in result.messages)
    assert result.messages[-1].content == "final answer"


def test_trim_keeps_last_turn_even_when_it_exceeds_budget():
    huge = "z" * 4000
    messages = [
        HumanMessage(content="old"),
        AIMessage(content="old-reply"),
        HumanMessage(content=huge),
        AIMessage(content="reply"),
    ]
    budget = prompt_token_budget(
        max_context_tokens=400,
        reserve_for_reply=100,
    )

    result = trim_messages(
        messages,
        model="qwen-turbo",
        max_context_tokens=400,
        reserve_for_reply=100,
    )

    assert len(result.messages) == 2
    assert result.messages[0].content == huge
    assert result.token_count > budget
    assert result.dropped_turns == 1
