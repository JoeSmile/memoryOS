"""Token usage metering protocol and embedded PG recorder (EP09 9.3)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.token_quota_reserve import TokenQuotaReserve, quota_reserve_amount
from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.token_usage_repository import TokenUsageRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TokenUsageSnapshot:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_mapping(cls, data: dict) -> TokenUsageSnapshot | None:
        if not isinstance(data, dict):
            return None
        prompt = int(data.get("prompt_tokens", 0) or 0)
        completion = int(data.get("completion_tokens", 0) or 0)
        total = int(data.get("total_tokens", prompt + completion) or 0)
        if prompt <= 0 and completion <= 0 and total <= 0:
            return None
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )

    def merged_with(self, other: TokenUsageSnapshot) -> TokenUsageSnapshot:
        return TokenUsageSnapshot(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


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
    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self._repo = TokenUsageRepository(db)
        self._reserve = TokenQuotaReserve(redis)

    @staticmethod
    def _utc_today() -> date:
        return datetime.now(timezone.utc).date()

    async def _committed_tokens_today(self, user_id: uuid.UUID) -> int:
        totals = await self._repo.sum_for_user_utc_day(user_id, self._utc_today())
        return totals.total_tokens

    async def reserve_for_completion(self, user_id: uuid.UUID, *, stream_id: str) -> int:
        """Reserve headroom before SSE; rejects when committed + in-flight would exceed quota."""
        if not settings.token_quota_enabled:
            return 0

        today = self._utc_today()
        pg_used = await self._committed_tokens_today(user_id)
        reserved = await self._reserve.try_reserve(
            user_id=user_id,
            day=today,
            stream_id=stream_id,
            pg_used=pg_used,
        )
        if not reserved:
            raise AppException(
                code=42902,
                message="token_quota_exceeded",
                status_code=429,
            )

        return quota_reserve_amount()

    async def release_reservation(self, user_id: uuid.UUID, *, stream_id: str) -> None:
        if not settings.token_quota_enabled:
            return
        await self._reserve.release(
            user_id=user_id,
            day=self._utc_today(),
            stream_id=stream_id,
        )

    async def today_totals(self, user_id: uuid.UUID) -> TokenUsageSnapshot:
        today = self._utc_today()
        totals = await self._repo.sum_for_user_utc_day(user_id, today)
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
