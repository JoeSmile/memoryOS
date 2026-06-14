from datetime import datetime
from typing import Literal, get_args
from uuid import UUID

from pydantic import BaseModel, Field

MemoryType = Literal["preference", "fact", "constraint"]
MEMORY_TYPES: frozenset[str] = frozenset(get_args(MemoryType))


class MemoryRead(BaseModel):
    id: UUID
    user_id: UUID
    memory_key: str = Field(max_length=128)
    memory_type: MemoryType
    content: str
    importance: float = Field(ge=0.0, le=1.0)
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
