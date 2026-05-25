import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import ConversationCache
from app.core.exceptions import AppException
from app.models import Conversation
from app.repositories import ConversationRepository, UserRepository
from app.schemas.conversation import ConversationRead


class ConversationService:
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis | None = None,
    ) -> None:
        self.users = UserRepository(db)
        self.conversations = ConversationRepository(db)
        self.cache = ConversationCache(redis)

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

    async def invalidate_list_cache(self, user_id: uuid.UUID) -> None:
        """在 DB commit 之后调用，避免并发下用未提交数据回填缓存。"""
        await self.cache.invalidate(user_id)
