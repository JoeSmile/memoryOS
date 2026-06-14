"""MemoryRepository helpers (EP06)."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.memory import Memory
from app.repositories.memory_repository import MemoryRepository, _validate_memory_type


def test_validate_memory_type_rejects_unknown():
    with pytest.raises(ValueError, match="invalid memory_type"):
        _validate_memory_type("opinion")


@pytest.mark.asyncio
async def test_upsert_preserves_expires_at_when_omitted():
    user_id = uuid4()
    expires_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    existing = Memory(
        id=uuid4(),
        user_id=user_id,
        memory_key="fact:team",
        memory_type="fact",
        content="old",
        importance=Decimal("0.500"),
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    repo = MemoryRepository(db)
    repo.get_by_user_and_key = AsyncMock(return_value=existing)

    await repo.upsert(
        user_id=user_id,
        memory_key="fact:team",
        memory_type="fact",
        content="updated",
    )

    assert existing.content == "updated"
    assert existing.expires_at == expires_at


@pytest.mark.asyncio
async def test_upsert_clears_expires_at_when_explicitly_set_none():
    user_id = uuid4()
    existing = Memory(
        id=uuid4(),
        user_id=user_id,
        memory_key="fact:team",
        memory_type="fact",
        content="old",
        importance=Decimal("0.500"),
        expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    repo = MemoryRepository(db)
    repo.get_by_user_and_key = AsyncMock(return_value=existing)

    await repo.upsert(
        user_id=user_id,
        memory_key="fact:team",
        memory_type="fact",
        content="updated",
        expires_at=None,
    )

    assert existing.expires_at is None
