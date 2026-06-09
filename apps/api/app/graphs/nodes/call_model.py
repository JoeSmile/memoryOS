from langchain_core.messages import AIMessage, BaseMessage

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.nodes.mock_model import mock_invoke
from app.graphs.prompts.rag_chat import build_rag_system_message
from app.graphs.prompts.unified_react import (
    build_unified_react_system_message,
    compute_rag_sufficient,
)
from app.schemas.knowledge import KnowledgeChunkHit
from app.tools import build_tool_registry


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


def _resolve_rag_sufficient(state: ChatState) -> bool:
    if "rag_sufficient" in state:
        return bool(state["rag_sufficient"])
    raw_chunks = state.get("retrieved_chunks") or []
    return compute_rag_sufficient(
        raw_chunks,
        min_score=settings.rag_chat_min_score,
    )


def _messages_with_system(state: ChatState) -> list[BaseMessage]:
    messages = list(state["messages"])
    if not settings.rag_chat_enabled:
        return messages

    raw_chunks = state.get("retrieved_chunks") or []
    hits = [KnowledgeChunkHit.model_validate(chunk) for chunk in raw_chunks]

    if settings.agent_tools_enabled:
        rag_sufficient = _resolve_rag_sufficient(state)
        system = build_unified_react_system_message(
            chunks=hits,
            rag_sufficient=rag_sufficient,
        )
    else:
        system = build_rag_system_message(hits)
    return [system, *messages]


async def _invoke_with_tools(messages: list[BaseMessage]) -> AIMessage:
    llm = _build_chat_openai(streaming=False)
    tools = build_tool_registry().list_openai_schemas()
    response = await llm.bind_tools(tools).ainvoke(messages)
    if isinstance(response, AIMessage):
        return response
    return AIMessage(content=str(response))


async def _stream_text_only(messages: list[BaseMessage]) -> AIMessage:
    llm = _build_chat_openai(streaming=True)
    parts: list[str] = []
    async for chunk in llm.astream(messages):
        text = _chunk_text(chunk)
        if text:
            parts.append(text)
    return AIMessage(content="".join(parts))


async def call_model(state: ChatState) -> dict:
    messages = _messages_with_system(state)
    rag_sufficient = _resolve_rag_sufficient(state)

    if settings.use_mock_llm:
        response = await mock_invoke(
            messages,
            rag_sufficient=rag_sufficient,
            agent_tools_enabled=settings.agent_tools_enabled,
        )
        return {"messages": [response]}

    if settings.agent_tools_enabled:
        response = await _invoke_with_tools(messages)
        return {"messages": [response]}

    response = await _stream_text_only(messages)
    return {"messages": [response]}
