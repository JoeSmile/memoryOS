import asyncio
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

MOCK_TOKEN_CHUNKS: list[str] = ["你", "好", "！"]
MOCK_ASSISTANT_TEXT = "".join(MOCK_TOKEN_CHUNKS)

MOCK_AFTER_TOOL_CHUNKS: list[str] = ["联", "网", "答", "案"]
MOCK_AFTER_TOOL_TEXT = "".join(MOCK_AFTER_TOOL_CHUNKS)

MOCK_TOKEN_USAGE: dict[str, int] = {
    "prompt_tokens": 48,
    "completion_tokens": len(MOCK_ASSISTANT_TEXT),
    "total_tokens": 48 + len(MOCK_ASSISTANT_TEXT),
}
MOCK_AFTER_TOOL_TOKEN_USAGE: dict[str, int] = {
    "prompt_tokens": 64,
    "completion_tokens": len(MOCK_AFTER_TOOL_TEXT),
    "total_tokens": 64 + len(MOCK_AFTER_TOOL_TEXT),
}

_MOCK_TAVILY_CALL_ID = "mock_call_tavily"


def _after_tool_round(messages: list[BaseMessage]) -> bool:
    return any(isinstance(message, ToolMessage) for message in messages)


async def mock_invoke(
    messages: list[BaseMessage],
    *,
    rag_sufficient: bool,
    agent_tools_enabled: bool,
) -> AIMessage:
    """Deterministic mock: sufficient RAG → text only; weak RAG → tool then text."""
    if not agent_tools_enabled or rag_sufficient:
        return AIMessage(
            content=MOCK_ASSISTANT_TEXT,
            response_metadata={"token_usage": dict(MOCK_TOKEN_USAGE)},
        )

    if _after_tool_round(messages):
        return AIMessage(
            content=MOCK_AFTER_TOOL_TEXT,
            response_metadata={"token_usage": dict(MOCK_AFTER_TOOL_TOKEN_USAGE)},
        )

    return AIMessage(
        content="",
        response_metadata={"token_usage": dict(MOCK_TOKEN_USAGE)},
        tool_calls=[
            {
                "name": "tavily_search",
                "args": {"query": "mock web search"},
                "id": _MOCK_TAVILY_CALL_ID,
                "type": "tool_call",
            }
        ],
    )


async def mock_stream_tokens() -> AsyncIterator[str]:
    for chunk in MOCK_TOKEN_CHUNKS:
        yield chunk


async def mock_stream_tokens_slow(
    delay_seconds: float = 0.35,
) -> AsyncIterator[str]:
    """Harness: leave time to cancel/disconnect mid-stream."""
    for chunk in MOCK_TOKEN_CHUNKS:
        await asyncio.sleep(delay_seconds)
        yield chunk
