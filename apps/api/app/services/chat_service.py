import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.cache.completion_turn_lock import CompletionTurnLock
from app.cache.stream_cancel_cache import StreamCancelCache
from app.cache.stream_cache import StreamCache
from app.core.exceptions import AppException
from app.graphs.chat_state import ChatState
from app.graphs.runner import ChatGraphRunner
from app.models import Message
from app.models.message import COMPLETION_COMPLETE, COMPLETION_INTERRUPTED
from app.repositories import MessageRepository
from app.services.conversation_service import ConversationService

class _ClientDisconnected(Exception):
    """Consumer closed the SSE connection (stop / tab close / proxy abort)."""


@dataclass
class CompletionStreamState:
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assistant_parts: list[str] = field(default_factory=list)
    rag_source_items: list[dict] | None = None
    stream_exhausted: bool = False
    disconnected: bool = False
    terminal_error: bool = False
    persisted: bool = False


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
        self.cancel_cache = StreamCancelCache(redis)
        self.turn_lock = CompletionTurnLock(redis)
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

    @staticmethod
    def _assistant_after_user(
        history: list[Message],
        user_message: Message,
    ) -> Message | None:
        for index, row in enumerate(history):
            if row.id == user_message.id and index + 1 < len(history):
                candidate = history[index + 1]
                if candidate.role == "assistant":
                    return candidate
                return None
        return None

    async def _remove_last_assistant_if_any(self, history: list[Message]) -> None:
        for row in reversed(history):
            if row.role == "assistant":
                await self.messages.delete_by_id(row.id)
                return

    async def _prepare_user_turn(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        client_message_id: uuid.UUID | None,
        regenerate: bool,
    ) -> None:
        if regenerate:
            history = await self.messages.list_by_conversation_id(conversation_id)
            if not any(row.role == "user" for row in history):
                raise AppException(
                    code=42201,
                    message="regenerate_requires_user_message",
                    status_code=422,
                )
            await self._remove_last_assistant_if_any(history)
            await self.conversations.touch_activity(conversation_id)
            await self.db.commit()
            await self.conversations.invalidate_list_cache(user_id)
            return

        if client_message_id is not None:
            existing = await self.messages.get_by_client_message_id(
                conversation_id,
                client_message_id,
            )
            if existing is not None:
                history = await self.messages.list_by_conversation_id(conversation_id)
                assistant = self._assistant_after_user(history, existing)
                if assistant is not None:
                    if assistant.completion_status == COMPLETION_COMPLETE:
                        raise AppException(
                            code=40902,
                            message="duplicate_message",
                            status_code=409,
                        )
                    await self.messages.delete_by_id(assistant.id)
                await self.conversations.touch_activity(conversation_id)
                await self.db.commit()
                await self.conversations.invalidate_list_cache(user_id)
                return

        await self.messages.create(
            conversation_id,
            "user",
            content,
            client_message_id=client_message_id,
        )
        await self.conversations.touch_activity(conversation_id)
        await self.db.commit()
        await self.conversations.invalidate_list_cache(user_id)

    async def prepare_completion_turn(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        client_message_id: uuid.UUID | None = None,
        regenerate: bool = False,
    ) -> None:
        await self.conversations.get_owned_conversation(conversation_id, user_id)
        await self._prepare_user_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            client_message_id=client_message_id,
            regenerate=regenerate,
        )
        if client_message_id is not None:
            acquired = await self.turn_lock.try_acquire(
                conversation_id,
                client_message_id,
            )
            if not acquired:
                raise AppException(
                    code=40902,
                    message="duplicate_message",
                    status_code=409,
                )

    async def release_turn_inflight_lock(
        self,
        conversation_id: uuid.UUID,
        client_message_id: uuid.UUID | None,
    ) -> None:
        if client_message_id is None:
            return
        await self.turn_lock.release(conversation_id, client_message_id)

    @staticmethod
    def _interrupted_content(
        full: str,
        visible: str | None,
        visible_length: int | None = None,
    ) -> str:
        if visible_length is not None:
            if visible_length <= 0:
                return ""
            return full[:visible_length] if len(full) >= visible_length else full
        if not visible:
            return full
        if not full:
            return visible
        if full.startswith(visible):
            return visible
        if visible.startswith(full):
            return full
        return visible if len(visible) <= len(full) else full

    async def cancel_stream(
        self,
        *,
        stream_id: str,
        user_id: uuid.UUID,
        visible_content: str | None = None,
        visible_length: int | None = None,
    ) -> None:
        owner = await self.cancel_cache.get_active_owner(stream_id)
        if owner is None:
            raise AppException(
                code=40401,
                message="stream_not_found",
                status_code=404,
            )

        if owner[1] != user_id:
            raise AppException(
                code=40401,
                message="stream_not_found",
                status_code=404,
            )

        if await self.cancel_cache.is_cancelled(stream_id):
            if visible_content is not None or visible_length is not None:
                await self.cancel_cache.update_visible_snapshot(
                    stream_id,
                    visible_content=visible_content,
                    visible_length=visible_length,
                )
            return

        await self.cancel_cache.set_cancelled(
            stream_id,
            visible_content=visible_content,
            visible_length=visible_length,
        )

    async def _iter_tokens_with_disconnect(
        self,
        state: ChatState,
        *,
        conversation_id: uuid.UUID,
        stream_id: str,
        request: Request | None,
    ) -> AsyncIterator[str]:
        """Delegate to runner; raise when HTTP client disconnects mid-stream."""
        async for token in self.runner.stream_tokens(
            state,
            thread_id=str(conversation_id),
            db=self.db,
            request=request,
            stream_id=stream_id,
            cancel_cache=self.cancel_cache,
        ):
            yield token

        if request is not None and await request.is_disconnected():
            raise _ClientDisconnected

    def new_completion_stream_state(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CompletionStreamState:
        return CompletionStreamState(
            conversation_id=conversation_id,
            user_id=user_id,
        )

    async def stream_completion_events(
        self,
        *,
        stream_state: CompletionStreamState,
        request: Request | None = None,
    ) -> AsyncIterator[dict]:
        history = await self.messages.list_by_conversation_id(
            stream_state.conversation_id,
        )
        graph_state = self._to_graph_state(stream_state.user_id, history)

        await self.cancel_cache.register_active(
            stream_state.stream_id,
            stream_state.conversation_id,
            stream_state.user_id,
        )
        yield {"event": "start", "data": {"stream_id": stream_state.stream_id}}

        sources_emitted = False

        try:
            async for token in self._iter_tokens_with_disconnect(
                graph_state,
                conversation_id=stream_state.conversation_id,
                stream_id=stream_state.stream_id,
                request=request,
            ):
                if not sources_emitted:
                    source_items = ChatGraphRunner.format_rag_source_items(
                        self.runner.last_retrieved_chunks,
                    )
                    if source_items:
                        stream_state.rag_source_items = source_items
                        yield {"event": "sources", "data": {"items": source_items}}
                    sources_emitted = True

                stream_state.assistant_parts.append(token)
                await self.stream_cache.append(
                    stream_state.conversation_id,
                    stream_state.stream_id,
                    token,
                )
                yield {"event": "token", "data": {"content": token}}

            if await self.cancel_cache.is_cancelled(stream_state.stream_id):
                stream_state.disconnected = True
            else:
                stream_state.stream_exhausted = True
        except _ClientDisconnected:
            stream_state.disconnected = True
        except asyncio.CancelledError:
            stream_state.disconnected = True
            raise
        except Exception:
            stream_state.terminal_error = True
            await self.stream_cache.delete(
                stream_state.conversation_id,
                stream_state.stream_id,
            )
            yield {"event": "error", "data": {"message": "stream_failed"}}

    async def finalize_completion_stream(
        self,
        stream_state: CompletionStreamState,
    ) -> uuid.UUID | None:
        """Always run from router finally — BFF may close before generator postamble."""
        visible_content = await self.cancel_cache.get_visible_content(
            stream_state.stream_id,
        )
        visible_length = await self.cancel_cache.get_visible_length(
            stream_state.stream_id,
        )
        await self.cancel_cache.clear(stream_state.stream_id)
        await self.stream_cache.delete(
            stream_state.conversation_id,
            stream_state.stream_id,
        )
        if (
            stream_state.persisted
            or stream_state.terminal_error
            or not stream_state.assistant_parts
        ):
            return None

        completion_status = (
            COMPLETION_COMPLETE
            if stream_state.stream_exhausted and not stream_state.disconnected
            else COMPLETION_INTERRUPTED
        )
        full_content = "".join(stream_state.assistant_parts)
        content = self._interrupted_content(
            full_content,
            visible_content,
            visible_length,
        )
        if not content:
            return None
        assistant = await self.messages.create(
            stream_state.conversation_id,
            "assistant",
            content,
            completion_status=completion_status,
        )
        await self.conversations.touch_activity(stream_state.conversation_id)
        await self.db.commit()
        await self.conversations.invalidate_list_cache(stream_state.user_id)
        stream_state.persisted = True
        return assistant.id
