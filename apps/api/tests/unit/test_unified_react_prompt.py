from uuid import uuid4

from app.graphs.prompts.unified_react import (
    build_unified_react_system_message,
    compute_rag_sufficient,
)
from app.schemas.knowledge import KnowledgeChunkHit


def test_compute_rag_sufficient_empty():
    assert compute_rag_sufficient([], min_score=0.35) is False


def test_compute_rag_sufficient_below_threshold():
    chunks = [{"score": 0.2, "content": "x", "external_id": "a", "collection": "c"}]
    assert compute_rag_sufficient(chunks, min_score=0.35) is False


def test_compute_rag_sufficient_at_threshold():
    chunks = [{"score": 0.35, "content": "x", "external_id": "a", "collection": "c"}]
    assert compute_rag_sufficient(chunks, min_score=0.35) is True


def test_build_unified_react_system_message_weak_mentions_tavily():
    message = build_unified_react_system_message(chunks=[], rag_sufficient=False)
    assert "tavily_search" in message.content
    assert "不足" in message.content


def test_build_unified_react_system_message_sufficient_mentions_priority():
    chunks = [
        KnowledgeChunkHit(
            external_id="wc-1",
            collection="samples",
            score=0.9,
            content="fact",
            document_id=uuid4(),
            entity_type="fact_card",
        ),
    ]
    message = build_unified_react_system_message(chunks=chunks, rag_sufficient=True)
    assert "tavily_search" in message.content
    assert "可能足够" in message.content
    assert "参考资料" in message.content
