"""Short-term context trimming: sliding turns within token budget (EP06)."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage

from app.services.memory.token_counter import count_messages_tokens


@dataclass(frozen=True)
class TrimResult:
    messages: list[BaseMessage]
    dropped_turns: int
    token_count: int


def prompt_token_budget(
    *,
    max_context_tokens: int,
    reserve_for_reply: int,
    reserved_prompt_tokens: int = 0,
    min_prompt_tokens: int = 256,
) -> int:
    """Tokens available for conversation history after reply and injected prompts."""
    budget = max_context_tokens - reserve_for_reply - reserved_prompt_tokens
    return max(budget, min_prompt_tokens)


def _turn_spans(messages: list[BaseMessage]) -> list[tuple[int, int]]:
    """Group messages into turns: Human-led, or a prefix block before the first Human."""
    if not messages:
        return []
    spans: list[tuple[int, int]] = []
    index = 0
    length = len(messages)
    while index < length:
        start = index
        if isinstance(messages[index], HumanMessage):
            index += 1
            while index < length and not isinstance(messages[index], HumanMessage):
                index += 1
        else:
            index += 1
            while index < length and not isinstance(messages[index], HumanMessage):
                index += 1
        spans.append((start, index))
    return spans


def _drop_leading_orphan_tools(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Remove leading ToolMessages left after trimming an incomplete ReAct round."""
    if not messages or not isinstance(messages[0], ToolMessage):
        return messages
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            return messages[index:]
    return messages[-1:]


def trim_messages(
    messages: list[BaseMessage],
    *,
    model: str,
    max_context_tokens: int,
    reserve_for_reply: int,
    reserved_prompt_tokens: int = 0,
) -> TrimResult:
    """
    Drop oldest turns until history fits the prompt budget.

    ``reserved_prompt_tokens`` reserves space for system/RAG/memory/summary blocks
    injected later in ``call_model`` (not yet in ``messages``).
    """
    if not messages:
        return TrimResult(messages=[], dropped_turns=0, token_count=0)

    budget = prompt_token_budget(
        max_context_tokens=max_context_tokens,
        reserve_for_reply=reserve_for_reply,
        reserved_prompt_tokens=reserved_prompt_tokens,
    )
    total_tokens = count_messages_tokens(messages, model=model)
    if total_tokens <= budget:
        return TrimResult(messages=list(messages), dropped_turns=0, token_count=total_tokens)

    spans = _turn_spans(messages)
    kept: list[BaseMessage] = []
    kept_tokens = 0
    kept_turn_count = 0

    for start, end in reversed(spans):
        turn = messages[start:end]
        turn_tokens = count_messages_tokens(turn, model=model)
        if not kept:
            kept = turn
            kept_tokens = turn_tokens
            kept_turn_count = 1
            continue
        if kept_tokens + turn_tokens <= budget:
            kept = turn + kept
            kept_tokens += turn_tokens
            kept_turn_count += 1
        else:
            break

    kept = _drop_leading_orphan_tools(kept)
    kept_tokens = count_messages_tokens(kept, model=model)
    dropped_turns = len(spans) - kept_turn_count

    return TrimResult(
        messages=kept,
        dropped_turns=dropped_turns,
        token_count=kept_tokens,
    )
