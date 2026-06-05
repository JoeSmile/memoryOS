from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatCompletionRequest(BaseModel):
    conversation_id: UUID
    content: str = Field(min_length=1)
