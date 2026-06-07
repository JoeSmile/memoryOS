from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    client_message_id: UUID | None = None
    completion_status: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatCompletionRequest(BaseModel):
    conversation_id: UUID
    content: str = Field(min_length=1)
    client_message_id: UUID | None = None
    regenerate: bool = False


class ChatCancelRequest(BaseModel):
    stream_id: UUID
    visible_content: str | None = Field(default=None, max_length=100_000)
