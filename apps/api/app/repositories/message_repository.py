import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


class MessageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        *,
        client_message_id: uuid.UUID | None = None,
        completion_status: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            client_message_id=client_message_id,
            completion_status=completion_status,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_by_client_message_id(
        self,
        conversation_id: uuid.UUID,
        client_message_id: uuid.UUID,
    ) -> Message | None:
        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.client_message_id == client_message_id,
                Message.role == "user",
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_id(self, message_id: uuid.UUID) -> None:
        await self.db.execute(delete(Message).where(Message.id == message_id))

    async def list_by_conversation_id(
        self,
        conversation_id: uuid.UUID,
    ) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
