import uuid
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.cache.stream_cache import StreamCache
from app.graphs.chat_state import ChatState
from app.graphs.runner import ChatGraphRunner
from app.models import Message
from app.repositories import MessageRepository
from app.services.conversation_service import ConversationService


class ChatService:
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis | None = None,
        runner: ChatGraphRunner | None = None,
    ) -> None:
        self.db = db
        self.conversations = ConversationService(db, redis=redis)
        self.messages = MessageRepository(db)
        self.stream_cache = StreamCache(redis)
        self.runner = runner if runner is not None else ChatGraphRunner()

    @staticmethod
    def _to_graph_state(user_id: uuid.UUID, history: list[Message]) -> ChatState:
        lc_messages: list = []
        for row in history:
            if row.role == "user":
                lc_messages.append(HumanMessage(content=row.content))
            elif row.role == "assistant":
                lc_messages.append(AIMessage(content=row.content))
        return ChatState(messages=lc_messages, user_id=str(user_id))

    async def stream_completion_events(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        request: Request | None = None,
    ) -> AsyncIterator[dict]:
        await self.conversations.get_owned_conversation(conversation_id, user_id)

        await self.messages.create(conversation_id, "user", content)
        await self.conversations.touch_activity(conversation_id)
        await self.db.commit()
        await self.conversations.invalidate_list_cache(user_id)

        history = await self.messages.list_by_conversation_id(conversation_id)
        state = self._to_graph_state(user_id, history)
        stream_id = str(uuid.uuid4())
        assistant_parts: list[str] = []

        try:
            async for token in self.runner.stream_tokens(
                state,
                thread_id=str(conversation_id),
            ):
                if request is not None and await request.is_disconnected():
                    await self.stream_cache.delete(conversation_id, stream_id)
                    return

                assistant_parts.append(token)
                await self.stream_cache.append(conversation_id, stream_id, token)
                yield {"event": "token", "data": {"content": token}}
        except Exception:
            await self.stream_cache.delete(conversation_id, stream_id)
            yield {"event": "error", "data": {"message": "stream_failed"}}
            return

        full = "".join(assistant_parts)
        assistant = await self.messages.create(conversation_id, "assistant", full)
        await self.conversations.touch_activity(conversation_id)
        await self.stream_cache.delete(conversation_id, stream_id)
        yield {
            "event": "done",
            "data": {
                "message_id": str(assistant.id),
                "stream_id": stream_id,
            },
        }
