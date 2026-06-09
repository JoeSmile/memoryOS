"""Unified ReAct system prompts: RAG context + tool guidance (EP05)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date
from typing import Any

from langchain_core.messages import SystemMessage

from app.graphs.prompts.rag_chat import build_rag_system_message
from app.schemas.knowledge import KnowledgeChunkHit

_YEAR_PATTERN = re.compile(r"(20\d{2})")

_TIME_CONTEXT = """\
时间语境：
- 用户 **未写明** 具体年份/日期时，默认指向 **现在 / 今年 / 今日** 的最新语境（而非往年资料）
- 用户写「今年 / 今日 / 现在」等，与上述默认等价
- 检索上下文若仅有往年、不能代表当前语境，视为 **不足**，须调用 tavily_search"""

_TOOL_GUIDANCE = """\
工具：
- tavily_search：搜索互联网公开信息。当知识库未覆盖用户问题中的年份/实体、或问题依赖最新/库外信息时使用；不要为已覆盖的内容重复搜索。

ReAct 要求：
- 先阅读下方「检索上下文」与用户问题，并应用「时间语境」规则
- 若检索上下文 **直接回答了** 用户问题（含年份、实体与默认时间语境一致），直接回答，无需调用工具
- 若检索仅命中相似但 **不同年份/过时** 的资料，或明显不足以回答，**必须** 调用 tavily_search，再根据工具结果回答
- 最终回答使用简洁中文；若依据知识库资料，正文后保留 Markdown「## 参考来源」章节（与现有 RAG 一致）"""

_SUFFICIENT_SUFFIX = """\
当前判定：知识库检索 **可能足够** 回答。请优先依据检索上下文；仅当明确不够时再调用 tavily_search。"""

_WEAK_SUFFIX = """\
当前判定：知识库检索 **不足** 或未命中。你 **应** 先调用 tavily_search 补充信息，再组织最终回答。"""


def _resolve_now_year(now_year: int | None) -> int:
    return now_year if now_year is not None else date.today().year


def _explicit_years_from_query(user_query: str) -> set[int]:
    return {int(match.group(1)) for match in _YEAR_PATTERN.finditer(user_query)}


def _years_in_text(text: str) -> set[int]:
    return {int(match.group(1)) for match in _YEAR_PATTERN.finditer(text)}


def _chunk_text_blob(chunk: dict[str, Any]) -> str:
    parts = [
        str(chunk.get("external_id") or ""),
        str(chunk.get("collection") or ""),
        str(chunk.get("content_preview") or ""),
        str(chunk.get("content") or ""),
    ]
    return " ".join(parts)


def _years_in_chunks(raw_chunks: Sequence[dict[str, Any]]) -> set[int]:
    years: set[int] = set()
    for chunk in raw_chunks:
        if isinstance(chunk, dict):
            years |= _years_in_text(_chunk_text_blob(chunk))
    return years


def _chunks_contain_all_years(
    raw_chunks: Sequence[dict[str, Any]],
    required_years: set[int],
) -> bool:
    if not required_years:
        return True
    blob = " ".join(_chunk_text_blob(chunk) for chunk in raw_chunks if isinstance(chunk, dict))
    return all(str(year) in blob for year in required_years)


def _passes_implicit_now_check(
    raw_chunks: Sequence[dict[str, Any]],
    *,
    now_year: int,
) -> bool:
    """Unstated time defaults to 现在/今年/今日 — fail when chunks only cite past years."""
    chunk_years = _years_in_chunks(raw_chunks)
    if not chunk_years:
        return True
    if now_year in chunk_years:
        return True
    return max(chunk_years) >= now_year


def _passes_temporal_relevance(
    user_query: str,
    raw_chunks: Sequence[dict[str, Any]],
    *,
    now_year: int | None = None,
) -> bool:
    resolved_now = _resolve_now_year(now_year)
    explicit_years = _explicit_years_from_query(user_query)
    if explicit_years:
        return _chunks_contain_all_years(raw_chunks, explicit_years)
    return _passes_implicit_now_check(raw_chunks, now_year=resolved_now)


def compute_rag_sufficient(
    raw_chunks: Sequence[dict[str, Any]],
    *,
    min_score: float,
    user_query: str | None = None,
    now_year: int | None = None,
) -> bool:
    """True when chunks meet score threshold and match explicit or implicit time context."""
    if not raw_chunks:
        return False
    best_score = 0.0
    for chunk in raw_chunks:
        if not isinstance(chunk, dict):
            continue
        score = chunk.get("score")
        if isinstance(score, (int, float)) and float(score) > best_score:
            best_score = float(score)
    if best_score < min_score:
        return False
    if user_query and not _passes_temporal_relevance(
        user_query,
        raw_chunks,
        now_year=now_year,
    ):
        return False
    return True


def build_unified_react_system_message(
    *,
    chunks: Sequence[KnowledgeChunkHit],
    rag_sufficient: bool,
) -> SystemMessage:
    """RAG grounding text plus ReAct / tavily_search guidance."""
    base = build_rag_system_message(chunks)
    suffix = _SUFFICIENT_SUFFIX if rag_sufficient else _WEAK_SUFFIX
    content = f"{base.content}\n\n{_TIME_CONTEXT}\n\n{_TOOL_GUIDANCE}\n\n{suffix}"
    return SystemMessage(content=content)
