"""summary_service scheduling and rolling merge (EP06)."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.config import Settings, settings
from app.models import Conversation, Message
from app.services.memory.summary_service import (
    build_rolling_summary_prompt,
    build_summary_prompt,
    generate_summary_text,
    messages_after_summary_updated_at,
    produce_summary_text,
    should_schedule_summary,
)


def _conversation(
    *,
    context_summary: str | None = None,
    summary_updated_at: datetime | None = None,
) -> Conversation:
    return Conversation(
        id=uuid4(),
        user_id=uuid4(),
        title="t",
        context_summary=context_summary,
        summary_updated_at=summary_updated_at,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _message(
    *,
    role: str,
    content: str,
    created_at: datetime,
) -> Message:
    return Message(
        id=uuid4(),
        conversation_id=uuid4(),
        role=role,
        content=content,
        created_at=created_at,
    )


def _settings(**overrides) -> Settings:
    base = {
        "memory_enabled": True,
        "summary_trigger_tokens": 512,
        "summary_increment_tokens": 128,
        "summary_cooldown_seconds": 300,
        "openai_api_key": None,
    }
    base.update(overrides)
    return Settings(**base)


def test_should_schedule_first_trigger_when_history_exceeds_threshold():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    conversation = _conversation()
    messages = [
        _message(role="user", content="x" * 2000, created_at=now),
        _message(role="assistant", content="y" * 2000, created_at=now),
    ]
    cfg = _settings(summary_trigger_tokens=512)

    decision = should_schedule_summary(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert decision.should_schedule is True
    assert decision.reason == "first_trigger"


def test_should_schedule_skips_within_cooldown():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    conversation = _conversation(
        context_summary="已有摘要",
        summary_updated_at=now - timedelta(seconds=60),
    )
    messages = [
        _message(role="user", content="新增-" + ("a" * 200), created_at=now),
        _message(role="assistant", content="回复-" + ("b" * 200), created_at=now),
    ]
    cfg = _settings(summary_cooldown_seconds=300, summary_increment_tokens=128)

    decision = should_schedule_summary(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert decision.should_schedule is False
    assert decision.reason == "cooldown"


def test_should_schedule_skips_when_increment_below_threshold():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    conversation = _conversation(
        context_summary="已有摘要",
        summary_updated_at=now - timedelta(seconds=400),
    )
    messages = [
        _message(role="user", content="短", created_at=now),
        _message(role="assistant", content="好", created_at=now),
    ]
    cfg = _settings(summary_increment_tokens=128)

    decision = should_schedule_summary(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert decision.should_schedule is False
    assert decision.reason == "increment_below_threshold"


def test_should_schedule_rolling_when_increment_and_cooldown_met():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    updated_at = now - timedelta(seconds=400)
    conversation = _conversation(
        context_summary="已有摘要",
        summary_updated_at=updated_at,
    )
    messages = [
        _message(role="user", content="u-" + ("a" * 120), created_at=updated_at),
        _message(
            role="user",
            content="新-" + ("b" * 800),
            created_at=now,
        ),
        _message(role="assistant", content="新回复-" + ("c" * 800), created_at=now),
    ]
    cfg = _settings(summary_increment_tokens=128)

    decision = should_schedule_summary(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert decision.should_schedule is True
    assert decision.reason == "rolling_update"


def test_messages_after_summary_updated_at_only_includes_new_turns():
    anchor = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
    later = datetime(2026, 6, 14, 11, 0, tzinfo=timezone.utc)
    messages = [
        _message(role="user", content="old", created_at=anchor),
        _message(role="assistant", content="old-reply", created_at=anchor),
        _message(role="user", content="new", created_at=later),
    ]

    scoped = messages_after_summary_updated_at(messages, anchor)

    assert len(scoped) == 1
    assert scoped[0].content == "new"


def test_build_summary_prompt_rolling_uses_existing_and_new_messages():
    anchor = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
    later = datetime(2026, 6, 14, 11, 0, tzinfo=timezone.utc)
    conversation = _conversation(
        context_summary="用户偏好简洁",
        summary_updated_at=anchor,
    )
    messages = [
        _message(role="user", content="old", created_at=anchor),
        _message(role="user", content="new question", created_at=later),
    ]

    prompt = build_summary_prompt(conversation, messages)

    assert "用户偏好简洁" in prompt
    assert "new question" in prompt
    assert "old" not in prompt


def test_build_rolling_summary_prompt_formats_roles():
    messages = [
        _message(
            role="user",
            content="问题",
            created_at=datetime.now(timezone.utc),
        ),
        _message(
            role="assistant",
            content="回答",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    prompt = build_rolling_summary_prompt("旧摘要", messages)
    assert "用户: 问题" in prompt
    assert "助手: 回答" in prompt


@pytest.mark.asyncio
async def test_generate_summary_text_mock_stub(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    text = await generate_summary_text("压缩这段对话")
    assert text.startswith("[mock-summary]")


@pytest.mark.asyncio
async def test_produce_summary_text_returns_none_when_not_scheduled():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    conversation = _conversation()
    messages = [_message(role="user", content="短", created_at=now)]
    cfg = _settings(summary_trigger_tokens=4096)

    result = await produce_summary_text(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert result is None


@pytest.mark.asyncio
async def test_produce_summary_text_generates_on_first_trigger():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    conversation = _conversation()
    messages = [
        _message(role="user", content="u-" + ("x" * 2000), created_at=now),
        _message(role="assistant", content="a-" + ("y" * 2000), created_at=now),
    ]
    cfg = _settings(summary_trigger_tokens=512)

    result = await produce_summary_text(
        conversation,
        messages,
        now=now,
        settings_=cfg,
    )

    assert result is not None
    assert result.startswith("[mock-summary]")
