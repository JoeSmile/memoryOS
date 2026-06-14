"""Memory context system prompts for chat (EP06)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import SystemMessage

SUMMARY_PREFIX = "[会话摘要]\n"
MEMORY_HEADING = "## 用户长期记忆"


def format_summary_block_text(summary: str | None) -> str | None:
    text = (summary or "").strip()
    if not text:
        return None
    return f"{SUMMARY_PREFIX}{text}"


def build_context_summary_system_message(summary: str | None) -> SystemMessage | None:
    block = format_summary_block_text(summary)
    if block is None:
        return None
    return SystemMessage(content=block)


def format_memory_snippets_block_text(
    snippets: Sequence[dict[str, Any]],
) -> str | None:
    if not snippets:
        return None
    lines: list[str] = [MEMORY_HEADING]
    for snippet in snippets:
        content = str(snippet.get("content", "")).strip()
        if not content:
            continue
        snippet_type = str(snippet.get("type", "memory"))
        lines.append(f"- ({snippet_type}) {content}")
    if len(lines) == 1:
        return None
    return "\n".join(lines)


def build_memory_snippets_system_message(
    snippets: Sequence[dict[str, Any]],
) -> SystemMessage | None:
    block = format_memory_snippets_block_text(snippets)
    if block is None:
        return None
    return SystemMessage(content=block)
