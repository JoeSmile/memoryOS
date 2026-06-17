"""Token usage metering and daily quota checks (EP09 9.3)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.token_usage_repository import TokenUsageRepository

logger = logging.getLogger(__name__)

TOKEN_QUOTA_EXCEEDED_KEY = "token_quota_exceeded"
DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE = "您今日的token量使用完请过几个小时后再试"


@dataclass(frozen=True, slots=True)
class TokenUsageSnapshot:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_mapping(cls, data: dict) -> TokenUsageSnapshot | None:
        if not isinstance(data, dict):
            return None
        prompt = int(
            data.get("prompt_tokens", data.get("input_tokens", 0)) or 0
        )
        completion = int(
            data.get("completion_tokens", data.get("output_tokens", 0)) or 0
        )
        total = int(data.get("total_tokens", prompt + completion) or 0)
        if prompt <= 0 and completion <= 0 and total <= 0:
            return None
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )

    def to_mapping(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def merged_with(self, other: TokenUsageSnapshot) -> TokenUsageSnapshot:
        return TokenUsageSnapshot(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


def usage_snapshot_from_ai_message(message: object) -> TokenUsageSnapshot | None:
    """Read provider usage before LangGraph strips AIMessage response_metadata."""
    if not isinstance(message, AIMessage):
        return None
    meta = getattr(message, "response_metadata", None) or {}
    if isinstance(meta, dict):
        raw = meta.get("token_usage") or meta.get("usage")
        if isinstance(raw, dict):
            snap = TokenUsageSnapshot.from_mapping(raw)
            if snap is not None:
                return snap
    usage_meta = getattr(message, "usage_metadata", None)
    if usage_meta is not None:
        if hasattr(usage_meta, "model_dump"):
            usage_meta = usage_meta.model_dump()
        if isinstance(usage_meta, dict):
            return TokenUsageSnapshot.from_mapping(usage_meta)
    return None


class UsageRecorder(Protocol):
    async def record_completion(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        usage: TokenUsageSnapshot,
        message_id: uuid.UUID | None = None,
    ) -> None: ...


class EmbeddedUsageRecorder:
    """Persist completion usage to PostgreSQL (embedded graph mode)."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = TokenUsageRepository(db)

    async def record_completion(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        usage: TokenUsageSnapshot,
        message_id: uuid.UUID | None = None,
    ) -> None:
        await self._repo.record(
            user_id=user_id,
            conversation_id=conversation_id,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            message_id=message_id,
        )


class TokenQuotaService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = TokenUsageRepository(db)

    @staticmethod
    def _utc_today() -> date:
        return datetime.now(timezone.utc).date()

    async def assert_under_daily_quota(self, user_id: uuid.UUID) -> None:
        """Reject before chat/demo-turn when today's committed usage reached quota."""
        if not settings.token_quota_enabled:
            return

        totals = await self._repo.sum_for_user_utc_day(user_id, self._utc_today())
        if totals.total_tokens >= settings.user_daily_token_quota:
            raise AppException(
                code=42902,
                message=TOKEN_QUOTA_EXCEEDED_KEY,
                status_code=429,
                data={"detail": DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE},
            )

    async def today_totals(self, user_id: uuid.UUID) -> TokenUsageSnapshot:
        totals = await self._repo.sum_for_user_utc_day(user_id, self._utc_today())
        return TokenUsageSnapshot(
            prompt_tokens=totals.prompt_tokens,
            completion_tokens=totals.completion_tokens,
            total_tokens=totals.total_tokens,
        )


async def record_completion_usage_safe(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    usage: TokenUsageSnapshot,
    message_id: uuid.UUID | None = None,
) -> None:
    try:
        await EmbeddedUsageRecorder(db).record_completion(
            user_id=user_id,
            conversation_id=conversation_id,
            usage=usage,
            message_id=message_id,
        )
    except Exception:
        logger.exception(
            "token_usage_record_failed user_id=%s conversation_id=%s",
            user_id,
            conversation_id,
        )
