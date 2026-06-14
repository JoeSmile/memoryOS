"""memory_context prompt builders (EP06)."""

from app.graphs.prompts.memory_context import (
    build_context_summary_system_message,
    build_memory_snippets_system_message,
    format_memory_snippets_block_text,
    format_summary_block_text,
)


def test_format_summary_block_text_empty():
    assert format_summary_block_text(None) is None
    assert format_summary_block_text("   ") is None


def test_build_context_summary_system_message():
    message = build_context_summary_system_message("用户偏好简洁。")
    assert message is not None
    assert message.content == "[会话摘要]\n用户偏好简洁。"


def test_build_memory_snippets_system_message():
    message = build_memory_snippets_system_message(
        [{"type": "preference", "content": "喜欢短句"}],
    )
    assert message is not None
    assert "## 用户长期记忆" in message.content
    assert "(preference)" in message.content


def test_format_memory_snippets_block_text_skips_empty_content():
    assert format_memory_snippets_block_text(
        [{"type": "fact", "content": ""}],
    ) is None
