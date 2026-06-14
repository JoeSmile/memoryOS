"""call_model memory context injection (EP06)."""

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.nodes.call_model import _messages_with_system


def test_messages_with_system_injects_summary_and_memory_when_rag_disabled(
    monkeypatch,
):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_long_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)

    state: ChatState = {
        "messages": [HumanMessage(content="你好")],
        "user_id": "u1",
        "context_summary": "用户偏好简洁回答。",
        "memory_snippets": [
            {"type": "preference", "content": "喜欢短句", "score": 0.9},
        ],
    }
    messages = _messages_with_system(state)

    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content.startswith("[会话摘要]")
    assert "简洁" in messages[0].content
    assert isinstance(messages[1], SystemMessage)
    assert "## 用户长期记忆" in messages[1].content
    assert "喜欢短句" in messages[1].content
    assert messages[2].content == "你好"


def test_messages_with_system_skips_memory_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", False)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)

    state: ChatState = {
        "messages": [HumanMessage(content="你好")],
        "user_id": "u1",
        "context_summary": "不应出现",
        "memory_snippets": [{"type": "fact", "content": "不应出现", "score": 1.0}],
    }
    messages = _messages_with_system(state)

    assert len(messages) == 1
    assert messages[0].content == "你好"


def test_messages_with_system_layers_memory_before_rag(monkeypatch):
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "memory_long_term_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", True)
    monkeypatch.setattr(settings, "agent_tools_enabled", False)

    state: ChatState = {
        "messages": [HumanMessage(content="今年世界杯")],
        "user_id": "u1",
        "context_summary": "用户关注世界杯。",
        "memory_snippets": [{"type": "fact", "content": "支持阿根廷", "score": 0.8}],
        "retrieved_chunks": [],
    }
    messages = _messages_with_system(state)

    assert len(messages) == 4
    assert messages[0].content.startswith("[会话摘要]")
    assert "## 用户长期记忆" in messages[1].content
    assert isinstance(messages[2], SystemMessage)
    assert "MemoryOS" in messages[2].content or "世界杯" in messages[2].content
    assert messages[3].content == "今年世界杯"
