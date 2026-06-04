from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage

MOCK_TOKEN_CHUNKS: list[str] = ["你", "好", "！"]
MOCK_ASSISTANT_TEXT = "".join(MOCK_TOKEN_CHUNKS)


async def mock_invoke(_messages: list[BaseMessage]) -> AIMessage:
    return AIMessage(content=MOCK_ASSISTANT_TEXT)


async def mock_stream_tokens() -> AsyncIterator[str]:
    for chunk in MOCK_TOKEN_CHUNKS:
        yield chunk
