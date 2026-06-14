"""Load long-term user memories into graph state (EP06)."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.repositories.memory_repository import MemoryRepository, SimilarMemoryRow
from app.services.embedding_service import EmbeddingService


def _last_human_message_text(messages: list[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text
    return None


def _distance_to_score(distance: float) -> float:
    return 1.0 - distance


def _snippet_from_row(row: SimilarMemoryRow) -> dict[str, Any]:
    memory = row.memory
    return {
        "type": memory.memory_type,
        "content": memory.content,
        "score": _distance_to_score(row.distance),
    }


async def load_user_memories(state: ChatState, config: RunnableConfig) -> dict:
    if not settings.memory_enabled or not settings.memory_long_term_enabled:
        return {"memory_snippets": []}

    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    if not isinstance(db, AsyncSession):
        return {"memory_snippets": []}

    query = _last_human_message_text(state.get("messages") or [])
    if not query:
        return {"memory_snippets": []}

    user_id_raw = state.get("user_id")
    if not user_id_raw:
        return {"memory_snippets": []}

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError:
        return {"memory_snippets": []}

    embeddings = EmbeddingService()
    query_vector = await embeddings.embed_query(query)
    repository = MemoryRepository(db)
    rows = await repository.search_similar_for_user(
        user_id,
        query_vector,
        top_k=settings.memory_long_term_top_k,
    )

    min_score = settings.memory_min_score
    snippets = [
        _snippet_from_row(row)
        for row in rows
        if _distance_to_score(row.distance) >= min_score
    ]
    return {"memory_snippets": snippets}
