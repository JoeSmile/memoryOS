import json
import logging
import uuid

from redis.asyncio import Redis

from app.cache.keys import conversation_list_key
from app.core.config import settings
from app.models import Conversation
from app.schemas.conversation import ConversationRead

logger = logging.getLogger(__name__)


class ConversationCache:
    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis
        self.ttl = settings.conversation_list_cache_ttl

    @property
    def enabled(self) -> bool:
        return self.redis is not None

    async def get_list(self, user_id: uuid.UUID) -> list[ConversationRead] | None:
        if not self.enabled:
            return None
        try:
            raw = await self.redis.get(conversation_list_key(user_id))
            if raw is None:
                return None
            items = json.loads(raw)
            return [ConversationRead.model_validate(item) for item in items]
        except Exception:
            logger.debug("conversation cache get failed", exc_info=True)
            return None

    async def set_list(
        self,
        user_id: uuid.UUID,
        conversations: list[Conversation],
    ) -> None:
        if not self.enabled:
            return
        try:
            payload = [
                ConversationRead.model_validate(c).model_dump(mode="json")
                for c in conversations
            ]
            await self.redis.setex(
                conversation_list_key(user_id),
                self.ttl,
                json.dumps(payload),
            )
        except Exception:
            logger.debug("conversation cache set failed", exc_info=True)

    async def invalidate(self, user_id: uuid.UUID) -> None:
        if not self.enabled:
            return
        try:
            await self.redis.delete(conversation_list_key(user_id))
        except Exception:
            logger.debug("conversation cache invalidate failed", exc_info=True)
