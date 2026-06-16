"""Retrieve World Cup knowledge chunks before chat generation."""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.services.knowledge_search_service import KnowledgeSearchService
from app.services.security.rag_sanitizer import sanitize_retrieved_knowledge_chunk


def _last_human_message_text(messages: list[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text
    return None


async def retrieve_knowledge(state: ChatState, config: RunnableConfig) -> dict:
    if not settings.rag_chat_enabled:
        return {"retrieved_chunks": []}

    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    if not isinstance(db, AsyncSession):
        return {"retrieved_chunks": []}

    query = _last_human_message_text(state["messages"])
    if not query:
        return {"retrieved_chunks": []}

    service = KnowledgeSearchService(db)
    result = await service.search(
        query,
        collection=settings.rag_chat_collection,
        top_k=settings.rag_chat_top_k,
    )
    min_score = settings.rag_chat_min_score
    filtered = [hit for hit in result.chunks if hit.score >= min_score]
    return {
        "retrieved_chunks": [
            sanitize_retrieved_knowledge_chunk(hit).model_dump(mode="json")
            for hit in filtered
        ],
    }
