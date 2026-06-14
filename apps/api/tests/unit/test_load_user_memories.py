"""load_user_memories graph node (EP06)."""

from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.graphs.nodes.load_user_memories import load_user_memories
from app.models.memory import Memory
from app.repositories.memory_repository import SimilarMemoryRow


@pytest.mark.asyncio
async def test_load_user_memories_skipped_when_long_term_disabled(monkeypatch):
    monkeypatch.setattr(settings, "memory_long_term_enabled", False)
    state = {
        "messages": [HumanMessage(content="hello")],
        "user_id": str(uuid4()),
    }
    result = await load_user_memories(state, {})
    assert result == {"memory_snippets": []}


@pytest.mark.asyncio
async def test_load_user_memories_returns_empty_without_db():
    state = {
        "messages": [HumanMessage(content="hello")],
        "user_id": str(uuid4()),
    }
    result = await load_user_memories(state, {"configurable": {}})
    assert result == {"memory_snippets": []}


@pytest.mark.asyncio
async def test_load_user_memories_returns_ranked_snippets(monkeypatch):
    user_id = uuid4()
    memory = Memory(
        id=uuid4(),
        user_id=user_id,
        memory_key="pref:style",
        memory_type="preference",
        content="喜欢简洁回答",
        importance=Decimal("0.800"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    rows = [
        SimilarMemoryRow(memory=memory, distance=0.1),
    ]

    mock_embeddings = MagicMock()
    mock_embeddings.embed_query = AsyncMock(return_value=[0.1] * 1024)

    mock_repository = MagicMock()
    mock_repository.search_similar_for_user = AsyncMock(return_value=rows)

    db = MagicMock()
    db.__class__ = AsyncSession

    with (
        patch(
            "app.graphs.nodes.load_user_memories.EmbeddingService",
            return_value=mock_embeddings,
        ),
        patch(
            "app.graphs.nodes.load_user_memories.MemoryRepository",
            return_value=mock_repository,
        ),
    ):
        result = await load_user_memories(
            {
                "messages": [HumanMessage(content="请简短回答")],
                "user_id": str(user_id),
            },
            {"configurable": {"db": db}},
        )

    assert len(result["memory_snippets"]) == 1
    snippet = result["memory_snippets"][0]
    assert snippet["type"] == "preference"
    assert snippet["content"] == "喜欢简洁回答"
    assert snippet["score"] == 0.9
    mock_repository.search_similar_for_user.assert_awaited_once()
    assert mock_repository.search_similar_for_user.await_args.kwargs["top_k"] == settings.memory_long_term_top_k


@pytest.mark.asyncio
async def test_load_user_memories_filters_below_min_score(monkeypatch):
    user_id = uuid4()
    memory = Memory(
        id=uuid4(),
        user_id=user_id,
        memory_key="pref:style",
        memory_type="preference",
        content="弱相关",
        importance=Decimal("0.500"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    rows = [SimilarMemoryRow(memory=memory, distance=0.9)]

    mock_embeddings = MagicMock()
    mock_embeddings.embed_query = AsyncMock(return_value=[0.1] * 1024)
    mock_repository = MagicMock()
    mock_repository.search_similar_for_user = AsyncMock(return_value=rows)
    db = MagicMock()
    db.__class__ = AsyncSession

    monkeypatch.setattr(settings, "memory_min_score", 0.35)

    with (
        patch(
            "app.graphs.nodes.load_user_memories.EmbeddingService",
            return_value=mock_embeddings,
        ),
        patch(
            "app.graphs.nodes.load_user_memories.MemoryRepository",
            return_value=mock_repository,
        ),
    ):
        result = await load_user_memories(
            {
                "messages": [HumanMessage(content="无关问题")],
                "user_id": str(user_id),
            },
            {"configurable": {"db": db}},
        )

    assert result["memory_snippets"] == []
