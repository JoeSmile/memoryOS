"""Unified ReAct system prompts: RAG context + tool guidance (EP05)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import SystemMessage

from app.graphs.prompts.rag_chat import build_rag_system_message
from app.schemas.knowledge import KnowledgeChunkHit

_TOOL_GUIDANCE = """\
工具：
- tavily_search：搜索互联网公开信息。仅在知识库检索不足以完整、准确回答时使用；不要为已覆盖的内容重复搜索。

ReAct 要求：
- 先阅读下方「检索上下文」与用户问题
- 若检索上下文足够，直接回答，无需调用工具
- 若检索不足或问题依赖最新/库外信息，调用 tavily_search，再根据工具结果回答
- 最终回答使用简洁中文；若依据知识库资料，正文后保留 Markdown「## 参考来源」章节（与现有 RAG 一致）"""

_SUFFICIENT_SUFFIX = """\
当前判定：知识库检索 **可能足够** 回答。请优先依据检索上下文；仅当明确不够时再调用 tavily_search。"""

_WEAK_SUFFIX = """\
当前判定：知识库检索 **不足** 或未命中。你 **应** 先调用 tavily_search 补充信息，再组织最终回答。"""


def compute_rag_sufficient(
    raw_chunks: Sequence[dict[str, Any]],
    *,
    min_score: float,
) -> bool:
    """True when at least one chunk meets the RAG min score threshold."""
    if not raw_chunks:
        return False
    best_score = 0.0
    for chunk in raw_chunks:
        if not isinstance(chunk, dict):
            continue
        score = chunk.get("score")
        if isinstance(score, (int, float)) and float(score) > best_score:
            best_score = float(score)
    return best_score >= min_score


def build_unified_react_system_message(
    *,
    chunks: Sequence[KnowledgeChunkHit],
    rag_sufficient: bool,
) -> SystemMessage:
    """RAG grounding text plus ReAct / tavily_search guidance."""
    base = build_rag_system_message(chunks)
    suffix = _SUFFICIENT_SUFFIX if rag_sufficient else _WEAK_SUFFIX
    content = f"{base.content}\n\n{_TOOL_GUIDANCE}\n\n{suffix}"
    return SystemMessage(content=content)
