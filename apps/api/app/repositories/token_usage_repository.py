import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_usage import TokenUsage


@dataclass(frozen=True, slots=True)
class TokenUsageTotals:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def utc_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Inclusive start, exclusive end for UTC calendar day aggregation."""
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


class TokenUsageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        message_id: uuid.UUID | None = None,
    ) -> TokenUsage:
        row = TokenUsage(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def sum_for_user_utc_day(
        self,
        user_id: uuid.UUID,
        day: date,
    ) -> TokenUsageTotals:
        day_start, day_end = utc_day_bounds(day)
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(TokenUsage.prompt_tokens), 0),
                func.coalesce(func.sum(TokenUsage.completion_tokens), 0),
                func.coalesce(func.sum(TokenUsage.total_tokens), 0),
            ).where(
                TokenUsage.user_id == user_id,
                TokenUsage.created_at >= day_start,
                TokenUsage.created_at < day_end,
            )
        )
        prompt, completion, total = result.one()
        return TokenUsageTotals(
            prompt_tokens=int(prompt),
            completion_tokens=int(completion),
            total_tokens=int(total),
        )
