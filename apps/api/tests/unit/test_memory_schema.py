"""Memory Pydantic schemas (EP06)."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.models.memory import Memory
from app.schemas.memory import MemoryRead


def test_memory_read_from_orm_excludes_embedding():
    row = Memory(
        id=uuid4(),
        user_id=uuid4(),
        memory_key="pref:style",
        memory_type="preference",
        content="喜欢简洁回答",
        importance=Decimal("0.800"),
        embedding=[0.1] * 1024,
        expires_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    payload = MemoryRead.model_validate(row)
    assert payload.memory_type == "preference"
    assert payload.importance == 0.8
    assert "embedding" not in payload.model_dump()
