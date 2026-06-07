import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import ConversationCache
from app.core.exceptions import AppException
from app.models import Conversation, Message
from app.repositories import (
    ConversationRepository,
    MessageRepository,
    UserRepository,
)
from app.schemas.conversation import ConversationRead
from app.schemas.message import MessageRead


class ConversationService:
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis | None = None,
    ) -> None:
        self.users = UserRepository(db)
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.cache = ConversationCache(redis)

    async def get_owned_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation:
        conversation = await self.conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise AppException(
                code=40401,
                message="conversation_not_found",
                status_code=404,
            )
        return conversation

    async def list_for_user(self, user_id: uuid.UUID) -> list[ConversationRead]:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException(code=40401, message="user_not_found", status_code=404)

        cached = await self.cache.get_list(user_id)
        if cached is not None:
            return cached

        rows = await self.conversations.list_by_user_id(user_id)
        await self.cache.set_list(user_id, rows)
        return [ConversationRead.model_validate(c) for c in rows]

    async def create(self, user_id: uuid.UUID, title: str) -> Conversation:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException(code=40401, message="user_not_found", status_code=404)
        return await self.conversations.create(user_id=user_id, title=title)

    async def create_with_first_message(
        self,
        user_id: uuid.UUID,
        title: str,
        content: str,
        *,
        role: str = "user",
    ) -> tuple[Conversation, Message]:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException(code=40401, message="user_not_found", status_code=404)
        conversation = await self.conversations.create(user_id=user_id, title=title)
        message = await self.messages.create(
            conversation_id=conversation.id,
            role=role,
            content=content,
        )
        await self.conversations.touch_updated_at(conversation.id)
        await self.conversations.db.refresh(conversation)
        return conversation, message

    async def touch_activity(self, conversation_id: uuid.UUID) -> None:
        """Bump updated_at when messages are persisted (resume /me ordering)."""
        await self.conversations.touch_updated_at(conversation_id)

    async def invalidate_list_cache(self, user_id: uuid.UUID) -> None:
        """在 DB commit 之后调用，避免并发下用未提交数据回填缓存。"""
        await self.cache.invalidate(user_id)

    async def list_messages_for_user(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[MessageRead]:
        await self.get_owned_conversation(conversation_id, user_id)
        rows = await self.messages.list_by_conversation_id(conversation_id)
        return [MessageRead.model_validate(m) for m in rows]
