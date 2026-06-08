from langchain_core.messages import AIMessage, BaseMessage

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.nodes.mock_model import mock_invoke
from app.graphs.prompts.rag_chat import build_rag_system_message
from app.schemas.knowledge import KnowledgeChunkHit


def _build_chat_openai(*, streaming: bool = True):
    from langchain_openai import ChatOpenAI

    kwargs: dict = {
        "model": settings.openai_model,
        "streaming": streaming,
    }
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    if settings.openai_api_base:
        kwargs["base_url"] = settings.openai_api_base
    return ChatOpenAI(**kwargs)


def _chunk_text(chunk: object) -> str:
    content = chunk.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


def _messages_with_rag_system(state: ChatState) -> list[BaseMessage]:
    messages = list(state["messages"])
    if not settings.rag_chat_enabled:
        return messages

    raw_chunks = state.get("retrieved_chunks") or []
    hits = [KnowledgeChunkHit.model_validate(chunk) for chunk in raw_chunks]
    rag_system = build_rag_system_message(hits)
    return [rag_system, *messages]


async def call_model(state: ChatState) -> dict:
    messages = _messages_with_rag_system(state)
    if settings.use_mock_llm:
        response = await mock_invoke(messages)
        return {"messages": [response]}

    llm = _build_chat_openai(streaming=True)
    parts: list[str] = []
    async for chunk in llm.astream(messages):
        text = _chunk_text(chunk)
        if text:
            parts.append(text)
    return {"messages": [AIMessage(content="".join(parts))]}
