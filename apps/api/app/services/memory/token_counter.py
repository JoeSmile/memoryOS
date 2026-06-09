"""Token counting for memory context budgets (EP06)."""

from __future__ import annotations

import tiktoken
from langchain_core.messages import BaseMessage

_FALLBACK_ENCODING = "cl100k_base"
# DashScope / qwen models are not in tiktoken's model map; cl100k_base is a stable proxy.
_MODEL_ENCODING_ALIASES: dict[str, str] = {
    "qwen-turbo": _FALLBACK_ENCODING,
    "qwen-plus": _FALLBACK_ENCODING,
    "qwen-max": _FALLBACK_ENCODING,
}


def encoding_for_model(model: str) -> tiktoken.Encoding:
    """Return a tiktoken encoding for the chat model name."""
    normalized = model.strip().lower()
    alias = _MODEL_ENCODING_ALIASES.get(normalized)
    if alias:
        return tiktoken.get_encoding(alias)
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding(_FALLBACK_ENCODING)


def count_text_tokens(text: str, *, model: str) -> int:
    if not text:
        return 0
    return len(encoding_for_model(model).encode(text))


def message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    if content is None:
        return ""
    return str(content)


def count_messages_tokens(messages: list[BaseMessage], *, model: str) -> int:
    return sum(count_text_tokens(message_text(message), model=model) for message in messages)
