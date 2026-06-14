"""MemoryService list and delete (EP06)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.models.memory import Memory
from app.services.memory_service import MemoryService


def _memory(user_id: uuid.UUID) -> Memory:
    now = datetime.now(timezone.utc)
    return Memory(
        id=uuid.uuid4(),
        user_id=user_id,
        memory_key="preference:style",
        memory_type="preference",
        content="偏好简洁",
        importance=Decimal("0.500"),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_list_for_user_maps_memory_read():
    user_id = uuid.uuid4()
    row = _memory(user_id)
    db = MagicMock()
    service = MemoryService(db)
    service.memories.list_by_user_id = AsyncMock(return_value=[row])

    items = await service.list_for_user(user_id, limit=10, offset=0)

    assert len(items) == 1
    assert items[0].memory_key == "preference:style"
    assert items[0].content == "偏好简洁"
    service.memories.list_by_user_id.assert_awaited_once_with(
        user_id,
        limit=10,
        offset=0,
    )


@pytest.mark.asyncio
async def test_delete_for_user_raises_when_not_owned():
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    db = MagicMock()
    service = MemoryService(db)
    service.memories.get_by_id_for_user = AsyncMock(return_value=None)

    with pytest.raises(AppException) as exc_info:
        await service.delete_for_user(memory_id, user_id)

    assert exc_info.value.code == 40401
    assert exc_info.value.message == "memory_not_found"


@pytest.mark.asyncio
async def test_delete_for_user_deletes_owned_memory():
    user_id = uuid.uuid4()
    row = _memory(user_id)
    db = MagicMock()
    service = MemoryService(db)
    service.memories.get_by_id_for_user = AsyncMock(return_value=row)
    service.memories.delete_by_id = AsyncMock(return_value=True)

    await service.delete_for_user(row.id, user_id)

    service.memories.delete_by_id.assert_awaited_once_with(row.id)
