"""Rolling conversation summary scheduling and generation (EP06)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import Settings, settings
from app.core.database import AsyncSessionLocal
from app.models import Conversation, Message
from app.repositories import ConversationRepository, MessageRepository

logger = logging.getLogger(__name__)
from app.services.memory.token_counter import count_text_tokens

_SUMMARY_ROLES = frozenset({"user", "assistant"})
_MOCK_SUMMARY_PREFIX = "[mock-summary] "


@dataclass(frozen=True)
class SummaryScheduleDecision:
    should_schedule: bool
    reason: str


def messages_for_summary(messages: list[Message]) -> list[Message]:
    return [message for message in messages if message.role in _SUMMARY_ROLES]


def count_message_list_tokens(messages: list[Message], *, model: str) -> int:
    return sum(count_text_tokens(message.content, model=model) for message in messages)


def messages_after_summary_updated_at(
    messages: list[Message],
    summary_updated_at: datetime | None,
) -> list[Message]:
    scoped = messages_for_summary(messages)
    if summary_updated_at is None:
        return scoped
    return [
        message
        for message in scoped
        if message.created_at > summary_updated_at
    ]


def should_schedule_summary(
    conversation: Conversation,
    messages: list[Message],
    *,
    now: datetime | None = None,
    settings_: Settings | None = None,
) -> SummaryScheduleDecision:
    cfg = settings_ or settings
    if not cfg.memory_enabled:
        return SummaryScheduleDecision(False, "memory_disabled")

    model = cfg.openai_model
    chat_messages = messages_for_summary(messages)
    summary_text = (conversation.context_summary or "").strip()

    if not summary_text:
        total_tokens = count_message_list_tokens(chat_messages, model=model)
        if total_tokens > cfg.summary_trigger_tokens:
            return SummaryScheduleDecision(True, "first_trigger")
        return SummaryScheduleDecision(False, "below_first_trigger")

    current = now or datetime.now(timezone.utc)
    updated_at = conversation.summary_updated_at
    if updated_at is not None:
        elapsed_seconds = (current - updated_at).total_seconds()
        if elapsed_seconds < cfg.summary_cooldown_seconds:
            return SummaryScheduleDecision(False, "cooldown")

    incremental_messages = messages_after_summary_updated_at(messages, updated_at)
    incremental_tokens = count_message_list_tokens(incremental_messages, model=model)
    if incremental_tokens < cfg.summary_increment_tokens:
        return SummaryScheduleDecision(False, "increment_below_threshold")

    return SummaryScheduleDecision(True, "rolling_update")


def _format_messages_for_prompt(messages: list[Message]) -> str:
    lines: list[str] = []
    for message in messages:
        label = "用户" if message.role == "user" else "助手"
        lines.append(f"{label}: {message.content.strip()}")
    return "\n".join(lines)


def build_first_summary_prompt(messages: list[Message]) -> str:
    conversation_block = _format_messages_for_prompt(messages_for_summary(messages))
    return (
        "请将以下对话压缩为简洁的中文会话摘要。"
        "保留用户约束、待办与关键决策；删除重复与无关细节。"
        "只输出摘要正文，不要标题或 Markdown。\n\n"
        f"对话:\n{conversation_block}"
    )


def build_rolling_summary_prompt(
    existing_summary: str,
    new_messages: list[Message],
) -> str:
    new_block = _format_messages_for_prompt(new_messages)
    return (
        "请将现有摘要与新增对话合并为更短的中文 rolling 摘要。"
        "保留用户约束、待办与关键决策；删除重复与无关细节。"
        "只输出摘要正文，不要标题或 Markdown。\n\n"
        f"现有摘要:\n{existing_summary.strip()}\n\n"
        f"新增对话:\n{new_block}"
    )


def build_summary_prompt(
    conversation: Conversation,
    messages: list[Message],
) -> str:
    summary_text = (conversation.context_summary or "").strip()
    if not summary_text:
        return build_first_summary_prompt(messages)

    new_messages = messages_after_summary_updated_at(
        messages,
        conversation.summary_updated_at,
    )
    return build_rolling_summary_prompt(summary_text, new_messages)


async def generate_summary_text(prompt: str, *, settings_: Settings | None = None) -> str:
    cfg = settings_ or settings
    if cfg.use_mock_llm:
        trimmed = prompt.strip()
        if len(trimmed) > 240:
            trimmed = f"{trimmed[:240]}…"
        return f"{_MOCK_SUMMARY_PREFIX}{trimmed}"

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
                content="你是会话摘要助手，输出简洁中文摘要，保留用户约束与待办。",
            ),
            HumanMessage(content=prompt),
        ]
    )
    content = response.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


async def produce_summary_text(
    conversation: Conversation,
    messages: list[Message],
    *,
    now: datetime | None = None,
    settings_: Settings | None = None,
) -> str | None:
    decision = should_schedule_summary(
        conversation,
        messages,
        now=now,
        settings_=settings_,
    )
    if not decision.should_schedule:
        return None
    prompt = build_summary_prompt(conversation, messages)
    return await generate_summary_text(prompt, settings_=settings_ or settings)


async def run_summary_background(conversation_id: uuid.UUID) -> None:
    """Background job: produce rolling summary and persist when still warranted."""
    async with AsyncSessionLocal() as db:
        conversations = ConversationRepository(db)
        messages_repo = MessageRepository(db)
        conversation = await conversations.get_by_id(conversation_id)
        if conversation is None:
            return

        all_messages = await messages_repo.list_by_conversation_id(conversation_id)
        summary_text = await produce_summary_text(conversation, all_messages)
        if summary_text is None:
            return

        now = datetime.now(timezone.utc)
        await conversations.update_context_summary(
            conversation_id,
            summary_text,
            now,
        )
        await db.commit()
        logger.info("conversation summary updated conversation_id=%s", conversation_id)
