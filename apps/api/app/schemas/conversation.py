from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    user_id: UUID
    title: str = Field(default="", max_length=500)
    initial_message: str | None = Field(default=None, min_length=1)


class ConversationRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    context_summary: str | None = None
    summary_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
