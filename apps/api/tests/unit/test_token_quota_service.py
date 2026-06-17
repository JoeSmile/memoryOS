"""Token quota service unit tests (EP09 4.3 redo)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.token_usage_repository import TokenUsageTotals
from app.services.token_quota_service import (
    DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE,
    TOKEN_QUOTA_EXCEEDED_KEY,
    TokenQuotaService,
    TokenUsageSnapshot,
    usage_snapshot_from_ai_message,
)


@pytest.mark.asyncio
async def test_assert_under_daily_quota_skipped_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", False)
    db = MagicMock()
    service = TokenQuotaService(db)
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock()

    await service.assert_under_daily_quota(uuid.uuid4())
    service._repo.sum_for_user_utc_day.assert_not_called()


@pytest.mark.asyncio
async def test_assert_under_daily_quota_raises_42902_when_at_quota(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100)

    service = TokenQuotaService(MagicMock())
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock(
        return_value=TokenUsageTotals(
            prompt_tokens=80,
            completion_tokens=20,
            total_tokens=100,
        )
    )

    with pytest.raises(AppException) as exc:
        await service.assert_under_daily_quota(uuid.uuid4())
    assert exc.value.code == 42902
    assert exc.value.message == TOKEN_QUOTA_EXCEEDED_KEY
    assert exc.value.data == {"detail": DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE}


@pytest.mark.asyncio
async def test_assert_under_daily_quota_allows_when_below_quota(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100)

    service = TokenQuotaService(MagicMock())
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock(
        return_value=TokenUsageTotals(
            prompt_tokens=40,
            completion_tokens=8,
            total_tokens=48,
        )
    )

    await service.assert_under_daily_quota(uuid.uuid4())


def test_token_usage_snapshot_from_mapping():
    usage = TokenUsageSnapshot.from_mapping(
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    )
    assert usage == TokenUsageSnapshot(10, 5, 15)


def test_token_usage_snapshot_from_usage_metadata_keys():
    usage = TokenUsageSnapshot.from_mapping(
        {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    )
    assert usage == TokenUsageSnapshot(10, 5, 15)


def test_usage_snapshot_from_ai_message_reads_response_metadata():
    from langchain_core.messages import AIMessage

    message = AIMessage(
        content="x",
        response_metadata={
            "token_usage": {
                "prompt_tokens": 12,
                "completion_tokens": 3,
                "total_tokens": 15,
            }
        },
    )
    assert usage_snapshot_from_ai_message(message) == TokenUsageSnapshot(12, 3, 15)
