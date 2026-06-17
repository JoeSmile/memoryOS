"""Token quota service unit tests (EP09 4.2)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.token_usage_repository import TokenUsageTotals
from app.services.token_quota_service import TokenQuotaService, TokenUsageSnapshot


@pytest.mark.asyncio
async def test_reserve_for_completion_skipped_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", False)
    db = MagicMock()
    service = TokenQuotaService(db)
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock()
    service._reserve = MagicMock()
    service._reserve.try_reserve = AsyncMock()

    reserved = await service.reserve_for_completion(uuid.uuid4(), stream_id="s1")
    assert reserved == 0
    service._repo.sum_for_user_utc_day.assert_not_called()
    service._reserve.try_reserve.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_for_completion_raises_42902_when_committed_at_quota(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100)
    monkeypatch.setattr(settings, "token_quota_request_reserve", 51)

    db = MagicMock()
    service = TokenQuotaService(db)
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock(
        return_value=TokenUsageTotals(
            prompt_tokens=80,
            completion_tokens=20,
            total_tokens=100,
        )
    )
    service._reserve = MagicMock()
    service._reserve.try_reserve = AsyncMock(return_value=False)

    with pytest.raises(AppException) as exc:
        await service.reserve_for_completion(uuid.uuid4(), stream_id="s1")
    assert exc.value.code == 42902
    assert exc.value.message == "token_quota_exceeded"


@pytest.mark.asyncio
async def test_reserve_for_completion_allows_when_one_token_below_quota(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100)
    monkeypatch.setattr(settings, "token_quota_request_reserve", 51)

    db = MagicMock()
    service = TokenQuotaService(db)
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock(
        return_value=TokenUsageTotals(
            prompt_tokens=40,
            completion_tokens=8,
            total_tokens=48,
        )
    )
    service._reserve = MagicMock()
    service._reserve.try_reserve = AsyncMock(return_value=True)

    reserved = await service.reserve_for_completion(uuid.uuid4(), stream_id="s1")
    assert reserved == 51
    service._reserve.try_reserve.assert_awaited_once()


@pytest.mark.asyncio
async def test_reserve_for_completion_rejects_near_quota_would_exceed(monkeypatch):
    """used=99_949 + reserve=51 > quota=100_000 — blocked before stream."""
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100_000)
    monkeypatch.setattr(settings, "token_quota_request_reserve", 51)

    db = MagicMock()
    service = TokenQuotaService(db)
    service._repo = MagicMock()
    service._repo.sum_for_user_utc_day = AsyncMock(
        return_value=TokenUsageTotals(
            prompt_tokens=90_000,
            completion_tokens=9_949,
            total_tokens=99_949,
        )
    )
    service._reserve = MagicMock()
    service._reserve.try_reserve = AsyncMock(return_value=False)

    with pytest.raises(AppException) as exc:
        await service.reserve_for_completion(uuid.uuid4(), stream_id="s1")
    assert exc.value.code == 42902


@pytest.mark.asyncio
async def test_reserve_for_completion_blocks_second_inflight_request(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    monkeypatch.setattr(settings, "user_daily_token_quota", 100)
    monkeypatch.setattr(settings, "token_quota_request_reserve", 51)

    from app.cache.token_quota_reserve import TokenQuotaReserve

    user_id = uuid.uuid4()
    day = TokenQuotaService._utc_today()
    reserve = TokenQuotaReserve(None)

    first = await reserve.try_reserve(
        user_id=user_id,
        day=day,
        stream_id="stream-a",
        pg_used=0,
    )
    second = await reserve.try_reserve(
        user_id=user_id,
        day=day,
        stream_id="stream-b",
        pg_used=0,
    )
    assert first is True
    assert second is False

    await reserve.release(user_id=user_id, day=day, stream_id="stream-a")
    third = await reserve.try_reserve(
        user_id=user_id,
        day=day,
        stream_id="stream-c",
        pg_used=0,
    )
    assert third is True


def test_token_usage_snapshot_from_mapping():
    usage = TokenUsageSnapshot.from_mapping(
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    )
    assert usage == TokenUsageSnapshot(10, 5, 15)
