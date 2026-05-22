import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Conversation
from app.repositories import ConversationRepository, UserRepository


class ConversationService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)
        self.conversations = ConversationRepository(db)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException(code=40401, message="user_not_found", status_code=404)
        return await self.conversations.list_by_user_id(user_id)

    async def create(self, user_id: uuid.UUID, title: str) -> Conversation:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException(code=40401, message="user_not_found", status_code=404)
        return await self.conversations.create(user_id=user_id, title=title)
