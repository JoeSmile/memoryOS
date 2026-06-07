import asyncio
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage

MOCK_TOKEN_CHUNKS: list[str] = ["你", "好", "！"]
MOCK_ASSISTANT_TEXT = "".join(MOCK_TOKEN_CHUNKS)


async def mock_invoke(_messages: list[BaseMessage]) -> AIMessage:
    return AIMessage(content=MOCK_ASSISTANT_TEXT)


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
