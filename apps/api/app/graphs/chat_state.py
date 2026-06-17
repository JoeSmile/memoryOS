from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict


def _merge_completion_usage(
    existing: dict[str, int] | None,
    update: dict[str, int] | None,
) -> dict[str, int] | None:
    if not update:
        return existing
    if not existing:
        return dict(update)
    return {
        "prompt_tokens": existing.get("prompt_tokens", 0)
        + update.get("prompt_tokens", 0),
        "completion_tokens": existing.get("completion_tokens", 0)
        + update.get("completion_tokens", 0),
        "total_tokens": existing.get("total_tokens", 0)
        + update.get("total_tokens", 0),
    }


class ChatState(TypedDict):
    """LangGraph state for EP02 chat + EP04 RAG retrieve + EP05 ReAct."""

    messages: Annotated[list, add_messages]
    user_id: str
    retrieved_chunks: NotRequired[list[dict[str, Any]]]
    rag_sufficient: NotRequired[bool]
    context_summary: NotRequired[str | None]
    memory_snippets: NotRequired[list[dict[str, Any]]]
    trim_stats: NotRequired[dict[str, Any]]
    completion_usage: Annotated[
        NotRequired[dict[str, int] | None],
        _merge_completion_usage,
    ]
