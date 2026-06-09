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


def test_compute_rag_sufficient_high_score_wrong_year():
    """WC-2022 hits must not satisfy a 2026 question (should trigger Tavily)."""
    chunks = [
        {
            "score": 0.92,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
        {
            "score": 0.88,
            "content": "2018年世界杯在法国夺冠。",
            "external_id": "tournament:WC-2018",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="2026年世界杯有多少支队伍？",
            now_year=2026,
        )
        is False
    )


def test_compute_rag_sufficient_jinnian_without_matching_chunks():
    chunks = [
        {
            "score": 0.9,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="今年世界杯有多少支队伍？",
            now_year=2026,
        )
        is False
    )


def test_compute_rag_sufficient_matching_year_still_sufficient():
    chunks = [
        {
            "score": 0.9,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="2022年世界杯有多少支队伍？",
            now_year=2026,
        )
        is True
    )


def test_compute_rag_sufficient_multi_year_requires_all():
    chunks = [
        {
            "score": 0.9,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="比较2022和2026世界杯参赛队伍数",
            now_year=2026,
        )
        is False
    )


def test_compute_rag_sufficient_unstated_time_stale_wc_chunks():
    """「世界杯」未写年份 → 默认今年；仅有往年 WC 资料 → insufficient."""
    chunks = [
        {
            "score": 0.91,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="世界杯有多少支队伍？",
            now_year=2026,
        )
        is False
    )


def test_compute_rag_sufficient_unstated_time_timeless_chunks():
    chunks = [
        {
            "score": 0.88,
            "content": "LangGraph 是基于图的状态机编排框架。",
            "external_id": "doc:langgraph-intro",
            "collection": "docs",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="LangGraph 是什么？",
            now_year=2026,
        )
        is True
    )


def test_compute_rag_sufficient_jintian_same_as_implicit_now():
    chunks = [
        {
            "score": 0.9,
            "content": "2022年世界杯有32支球队参加。",
            "external_id": "tournament:WC-2022",
            "collection": "samples",
        },
    ]
    assert (
        compute_rag_sufficient(
            chunks,
            min_score=0.35,
            user_query="今日世界杯有多少支队伍？",
            now_year=2026,
        )
        is False
    )


def test_build_unified_react_system_message_includes_time_context():
    message = build_unified_react_system_message(chunks=[], rag_sufficient=False)
    assert "时间语境" in message.content
    assert "今年" in message.content
    assert "今日" in message.content


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
