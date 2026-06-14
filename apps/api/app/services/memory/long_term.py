"""Long-term memory extraction, upsert, embed, and prune (EP06)."""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import AsyncSessionLocal
from app.models import Message
from app.models.memory import Memory
from app.repositories import ConversationRepository, MessageRepository
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MEMORY_TYPES
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

_EXTRACT_ROLES = frozenset({"user", "assistant"})
_MAX_EXTRACT_ITEMS = 5
_MEMORY_KEY_MAX_LEN = 128
_MOCK_EXTRACT_MARKER = "[mock-extract]"
_SLUG_RE = re.compile(r"[^\w]+", re.UNICODE)


@dataclass(frozen=True)
class ExtractedMemoryItem:
    memory_key: str
    memory_type: str
    content: str
    importance: float
    expires_at: datetime | None = None


def messages_for_extract(messages: list[Message]) -> list[Message]:
    return [message for message in messages if message.role in _EXTRACT_ROLES]


def normalize_slug(raw: str) -> str:
    text = raw.strip().lower()
    if not text:
        return ""
    slug = _SLUG_RE.sub("_", text).strip("_")
    return slug or ""


def memory_key_for_item(memory_type: str, raw_key: str) -> str:
    slug = normalize_slug(raw_key) or "item"
    prefix = f"{memory_type}:"
    combined = f"{prefix}{slug}"
    if len(combined) <= _MEMORY_KEY_MAX_LEN:
        return combined
    max_slug_len = _MEMORY_KEY_MAX_LEN - len(prefix)
    return f"{prefix}{slug[:max_slug_len]}"


def _format_messages_for_prompt(messages: list[Message]) -> str:
    lines: list[str] = []
    for message in messages:
        label = "用户" if message.role == "user" else "助手"
        lines.append(f"{label}: {message.content.strip()}")
    return "\n".join(lines)


def build_extract_prompt(
    messages: list[Message],
    *,
    context_summary: str | None = None,
) -> str:
    conversation_block = _format_messages_for_prompt(messages_for_extract(messages))
    summary_block = ""
    if context_summary and context_summary.strip():
        summary_block = f"会话摘要:\n{context_summary.strip()}\n\n"
    return (
        "从以下对话中抽取用户长期记忆，输出 JSON 数组（最多 "
        f"{_MAX_EXTRACT_ITEMS} 条）。每条字段："
        "key（简短标识）、type（preference|fact|constraint）、"
        "content（中文陈述）、importance（0-1 浮点）、"
        "expires_at（可选 ISO8601 或 null）。"
        "只输出 JSON，不要 Markdown。\n\n"
        f"{summary_block}"
        f"对话:\n{conversation_block}"
    )


def _clamp_importance(value: Any) -> float:
    try:
        importance = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, importance))


def _parse_expires_at(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_extract_json(raw: str) -> list[ExtractedMemoryItem]:
    text = raw.strip()
    if not text:
        return []

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    payload = json.loads(text)
    if not isinstance(payload, list):
        return []

    items: list[ExtractedMemoryItem] = []
    for entry in payload[:_MAX_EXTRACT_ITEMS]:
        if not isinstance(entry, dict):
            continue
        memory_type = str(entry.get("type") or "").strip().lower()
        if memory_type not in MEMORY_TYPES:
            continue
        content = str(entry.get("content") or "").strip()
        if not content:
            continue
        raw_key = str(entry.get("key") or content[:32]).strip()
        items.append(
            ExtractedMemoryItem(
                memory_key=memory_key_for_item(memory_type, raw_key),
                memory_type=memory_type,
                content=content,
                importance=_clamp_importance(entry.get("importance")),
                expires_at=_parse_expires_at(entry.get("expires_at")),
            )
        )
    return items


def _mock_extract_json(prompt: str) -> str:
    snippet = prompt.strip()
    if len(snippet) > 160:
        snippet = f"{snippet[:160]}…"
    return json.dumps(
        [
            {
                "key": "mock-extract",
                "type": "preference",
                "content": f"{_MOCK_EXTRACT_MARKER} {snippet}",
                "importance": 0.5,
            }
        ],
        ensure_ascii=False,
    )


async def call_extract_llm(prompt: str, *, settings_: Settings | None = None) -> str:
    cfg = settings_ or settings
    if cfg.use_mock_llm:
        return _mock_extract_json(prompt)

    from langchain_openai import ChatOpenAI

    kwargs: dict = {"model": cfg.openai_model, "streaming": False}
    if cfg.openai_api_key:
        kwargs["api_key"] = cfg.openai_api_key
    if cfg.openai_api_base:
        kwargs["base_url"] = cfg.openai_api_base

    llm = ChatOpenAI(**kwargs)
    response = await llm.ainvoke(
        [
            SystemMessage(
                content="你是记忆抽取助手，只输出合法 JSON 数组，不要解释。",
            ),
            HumanMessage(content=prompt),
        ]
    )
    content = response.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


async def upsert_extracted_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    items: list[ExtractedMemoryItem],
) -> int:
    if not items:
        return 0

    embeddings = EmbeddingService()
    vectors = await embeddings.embed_texts([item.content for item in items])
    repository = MemoryRepository(db)

    for item, vector in zip(items, vectors, strict=True):
        await repository.upsert(
            user_id=user_id,
            memory_key=item.memory_key,
            memory_type=item.memory_type,
            content=item.content,
            importance=Decimal(str(item.importance)),
            embedding=vector,
            expires_at=item.expires_at,
        )
    return len(items)


async def prune_user_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    settings_: Settings | None = None,
    now: datetime | None = None,
) -> int:
    cfg = settings_ or settings
    current = now or datetime.now(timezone.utc)
    threshold = Decimal(str(cfg.memory_prune_threshold))
    result = await db.execute(
        delete(Memory).where(
            Memory.user_id == user_id,
            or_(
                and_(Memory.expires_at.is_not(None), Memory.expires_at < current),
                Memory.importance < threshold,
            ),
        )
    )
    return int(result.rowcount or 0)


async def extract_and_persist_memories(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    *,
    settings_: Settings | None = None,
) -> int:
    cfg = settings_ or settings
    if not cfg.memory_enabled or not cfg.memory_long_term_enabled:
        return 0

    async with AsyncSessionLocal() as db:
        conversations = ConversationRepository(db)
        messages_repo = MessageRepository(db)
        conversation = await conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return 0

        messages = await messages_repo.list_by_conversation_id(conversation_id)
        prompt = build_extract_prompt(
            messages,
            context_summary=conversation.context_summary,
        )
        raw = await call_extract_llm(prompt, settings_=cfg)
        items = parse_extract_json(raw)
        if not items:
            await prune_user_memories(db, user_id, settings_=cfg)
            await db.commit()
            return 0

        upserted = await upsert_extracted_memories(db, user_id, items)
        await prune_user_memories(db, user_id, settings_=cfg)
        await db.commit()
        logger.info(
            "long-term memories extracted user_id=%s conversation_id=%s count=%s",
            user_id,
            conversation_id,
            upserted,
        )
        return upserted


async def run_extract_background(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    await extract_and_persist_memories(user_id, conversation_id)
