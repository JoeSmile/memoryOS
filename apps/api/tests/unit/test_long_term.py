"""long_term memory extract, upsert, embed, and prune (EP06)."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings, settings
from app.models import Conversation, Message
from app.services.memory.long_term import (
    build_extract_prompt,
    call_extract_llm,
    extract_and_persist_memories,
    memory_key_for_item,
    parse_extract_json,
    prune_user_memories,
    upsert_extracted_memories,
    ExtractedMemoryItem,
)


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


def _message(role: str, content: str) -> Message:
    now = datetime.now(timezone.utc)
    return Message(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        role=role,
        content=content,
        created_at=now,
    )


def test_memory_key_for_item_normalizes_type_prefix():
    assert memory_key_for_item("fact", "Favorite Team") == "fact:favorite_team"


def test_parse_extract_json_validates_types_and_limits():
    raw = json.dumps(
        [
            {
                "key": "style",
                "type": "preference",
                "content": "偏好简洁",
                "importance": 0.8,
            },
            {
                "key": "bad",
                "type": "unknown",
                "content": "skip me",
            },
            {
                "key": "rule",
                "type": "constraint",
                "content": "不要表格",
                "importance": 1.5,
                "expires_at": "2030-01-01T00:00:00Z",
            },
        ],
        ensure_ascii=False,
    )

    items = parse_extract_json(raw)

    assert len(items) == 2
    assert items[0].memory_key == "preference:style"
    assert items[0].importance == 0.8
    assert items[1].memory_type == "constraint"
    assert items[1].importance == 1.0
    assert items[1].expires_at == datetime(2030, 1, 1, tzinfo=timezone.utc)


def test_build_extract_prompt_includes_summary():
    messages = [_message("user", "新问题")]
    prompt = build_extract_prompt(
        messages,
        context_summary="用户关注世界杯",
    )
    assert "用户关注世界杯" in prompt
    assert "新问题" in prompt


@pytest.mark.asyncio
async def test_call_extract_llm_mock_returns_json():
    text = await call_extract_llm("抽取对话")
    payload = json.loads(text)
    assert payload[0]["type"] == "preference"
    assert "[mock-extract]" in payload[0]["content"]


@pytest.mark.asyncio
async def test_upsert_extracted_memories_embeds_and_upserts(monkeypatch):
    user_id = uuid.uuid4()
    db = MagicMock()

    repo_upsert = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.upsert = repo_upsert
    monkeypatch.setattr(
        "app.services.memory.long_term.MemoryRepository",
        lambda _db: mock_repo,
    )

    items = [
        ExtractedMemoryItem(
            memory_key="preference:style",
            memory_type="preference",
            content="偏好简洁回答",
            importance=0.6,
        ),
    ]

    count = await upsert_extracted_memories(db, user_id, items)

    assert count == 1
    repo_upsert.assert_awaited_once()
    kwargs = repo_upsert.await_args.kwargs
    assert kwargs["memory_key"] == "preference:style"
    assert kwargs["embedding"] is not None
    assert len(kwargs["embedding"]) > 0


@pytest.mark.asyncio
async def test_prune_user_memories_deletes_expired_and_low_importance():
    user_id = uuid.uuid4()
    db = MagicMock()
    result = MagicMock()
    result.rowcount = 2
    db.execute = AsyncMock(return_value=result)

    deleted = await prune_user_memories(db, user_id)

    assert deleted == 2
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_extract_and_persist_memories_disabled_returns_zero():
    cfg = Settings(
        memory_enabled=False,
        openai_api_key=None,
    )
    count = await extract_and_persist_memories(
        uuid.uuid4(),
        uuid.uuid4(),
        settings_=cfg,
    )
    assert count == 0


@pytest.mark.asyncio
async def test_extract_and_persist_memories_runs_pipeline(monkeypatch):
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="t",
        context_summary="摘要",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    messages = [
        _message("user", "我喜欢简洁回答"),
        _message("assistant", "好的"),
    ]

    session = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(rowcount=0))

    class FakeSessionCtx:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "app.services.memory.long_term.AsyncSessionLocal",
        lambda: FakeSessionCtx(),
    )

    conversations = MagicMock()
    conversations.get_by_id = AsyncMock(return_value=conversation)
    messages_repo = MagicMock()
    messages_repo.list_by_conversation_id = AsyncMock(return_value=messages)

    monkeypatch.setattr(
        "app.services.memory.long_term.ConversationRepository",
        lambda _db: conversations,
    )
    monkeypatch.setattr(
        "app.services.memory.long_term.MessageRepository",
        lambda _db: messages_repo,
    )

    upsert_mock = AsyncMock(return_value=1)
    monkeypatch.setattr(
        "app.services.memory.long_term.upsert_extracted_memories",
        upsert_mock,
    )
    prune_mock = AsyncMock(return_value=0)
    monkeypatch.setattr(
        "app.services.memory.long_term.prune_user_memories",
        prune_mock,
    )

    count = await extract_and_persist_memories(user_id, conversation_id)

    assert count == 1
    upsert_mock.assert_awaited_once()
    prune_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
