from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

# Keep in sync with web `CANCEL_VISIBLE_CONTENT_INLINE_MAX`.
CANCEL_VISIBLE_CONTENT_INLINE_MAX = 256


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
    visible_content: str | None = Field(
        default=None,
        max_length=CANCEL_VISIBLE_CONTENT_INLINE_MAX,
    )
    visible_length: int | None = Field(default=None, ge=0, le=100_000)

    @model_validator(mode="after")
    def normalize_visible_snapshot(self) -> Self:
        if (
            self.visible_content is not None
            and self.visible_length is not None
            and len(self.visible_content) != self.visible_length
        ):
            raise PydanticCustomError(
                "visible_content_length_mismatch",
                "visible_content must match visible_length",
            )
        if self.visible_content is not None and self.visible_length is None:
            self.visible_length = len(self.visible_content)
        return self
