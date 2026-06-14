"""Trim conversation history to token budget before RAG and model call (EP06)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.prompts.memory_context import (
    format_memory_snippets_block_text,
    format_summary_block_text,
)
from app.graphs.prompts.rag_chat import build_rag_system_message
from app.graphs.prompts.unified_react import build_unified_react_system_message
from app.schemas.knowledge import KnowledgeChunkHit
from app.services.memory.short_term import trim_messages
from app.services.memory.token_counter import count_text_tokens, message_text

# Retrieve runs after trim; reserve worst-case chunk payload (top_k × estimate).
_RAG_CHUNK_TOKEN_ESTIMATE = 256


def _summary_block_tokens(summary: str, *, model: str) -> int:
    block = format_summary_block_text(summary)
    if block is None:
        return 0
    return count_text_tokens(block, model=model)


def _memory_snippets_tokens(snippets: list[dict[str, Any]], *, model: str) -> int:
    block = format_memory_snippets_block_text(snippets)
    if block is None:
        return 0
    return count_text_tokens(block, model=model)


def _rag_system_reserve_tokens(*, model: str) -> int:
    if not settings.rag_chat_enabled:
        return 0
    if settings.agent_tools_enabled:
        system = build_unified_react_system_message(chunks=[], rag_sufficient=False)
    else:
        system = build_rag_system_message([])
    base_tokens = count_text_tokens(message_text(system), model=model)
    chunk_buffer = settings.rag_chat_top_k * _RAG_CHUNK_TOKEN_ESTIMATE
    return base_tokens + chunk_buffer


def _reserved_prompt_tokens(state: ChatState, *, model: str) -> int:
    summary = state.get("context_summary")
    summary_tokens = _summary_block_tokens(summary or "", model=model)

    snippets = state.get("memory_snippets") or []
    memory_tokens = _memory_snippets_tokens(snippets, model=model)

    rag_tokens = _rag_system_reserve_tokens(model=model)

    # Trim runs before retrieve_knowledge; chunks here are only from pre-filled state.
    chunks = state.get("retrieved_chunks") or []
    if chunks and settings.rag_chat_enabled:
        hits = [KnowledgeChunkHit.model_validate(chunk) for chunk in chunks]
        if settings.agent_tools_enabled:
            chunk_system = build_unified_react_system_message(
                chunks=hits,
                rag_sufficient=bool(state.get("rag_sufficient")),
            )
        else:
            chunk_system = build_rag_system_message(hits)
        rag_tokens = max(
            rag_tokens,
            count_text_tokens(message_text(chunk_system), model=model),
        )

    return summary_tokens + memory_tokens + rag_tokens


async def trim_history(state: ChatState) -> dict:
    if not settings.memory_enabled:
        return {
            "trim_stats": {
                "skipped": True,
                "reason": "memory_disabled",
            }
        }
    if not settings.memory_short_term_enabled:
        return {
            "trim_stats": {
                "skipped": True,
                "reason": "memory_short_term_disabled",
            }
        }

    messages: list[BaseMessage] = list(state.get("messages") or [])
    if not messages:
        return {
            "trim_stats": {
                "dropped_turns": 0,
                "token_count": 0,
                "trimmed": False,
            }
        }

    model = settings.openai_model
    reserved = _reserved_prompt_tokens(state, model=model)
    result = trim_messages(
        messages,
        model=model,
        max_context_tokens=settings.max_context_tokens,
        reserve_for_reply=settings.reserve_for_reply,
        reserved_prompt_tokens=reserved,
    )

    trim_stats = {
        "dropped_turns": result.dropped_turns,
        "token_count": result.token_count,
        "reserved_prompt_tokens": reserved,
        "trimmed": result.dropped_turns > 0 or len(result.messages) < len(messages),
    }

    if result.dropped_turns == 0 and len(result.messages) == len(messages):
        return {"trim_stats": trim_stats}

    return {
        "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *result.messages],
        "trim_stats": trim_stats,
    }
