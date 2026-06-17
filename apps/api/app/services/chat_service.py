import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks
from starlette.requests import Request

from app.cache.completion_turn_lock import CompletionTurnLock
from app.cache.stream_cancel_cache import StreamCancelCache
from app.cache.stream_cache import StreamCache
from app.core.exceptions import AppException
from app.graphs.chat_state import ChatState
from app.graphs.runner import ChatGraphRunner, RunnerStreamEvent
from app.models import Message
from app.models.message import COMPLETION_COMPLETE, COMPLETION_INTERRUPTED
from app.repositories import MessageRepository
from app.schemas.message import TOOL_STEP_SUMMARY_MAX_LEN
from app.services.conversation_service import ConversationService
from app.services.security.content_validator import assert_chat_content_length
from app.services.security.user_input_guard import run_user_input_guards
from app.core.config import settings
from app.services.memory.long_term import run_extract_background
from app.services.memory.summary_service import (
    run_summary_background,
    should_schedule_summary,
)
from app.services.token_quota_service import (
    TokenQuotaService,
    TokenUsageSnapshot,
    record_completion_usage_safe,
)

logger = logging.getLogger(__name__)


class _ClientDisconnected(Exception):
    """Consumer closed the SSE connection (stop / tab close / proxy abort)."""


@dataclass
class CompletionStreamState:
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assistant_parts: list[str] = field(default_factory=list)
    rag_source_items: list[dict] | None = None
    tool_steps: list[dict] = field(default_factory=list)
    stream_exhausted: bool = False
    disconnected: bool = False
    terminal_error: bool = False
    persisted: bool = False
    usage_recorded: bool = False
    usage: TokenUsageSnapshot | None = None


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
    def _to_graph_state(
        user_id: uuid.UUID,
        history: list[Message],
        *,
        context_summary: str | None = None,
    ) -> ChatState:
        lc_messages: list = []
        for row in history:
            if row.role == "user":
                lc_messages.append(HumanMessage(content=row.content))
            elif row.role == "assistant":
                lc_messages.append(AIMessage(content=row.content))
        return ChatState(
            messages=lc_messages,
            user_id=str(user_id),
            context_summary=context_summary,
        )

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
            for row in reversed(history):
                if row.role == "user":
                    assert_chat_content_length(row.content)
                    run_user_input_guards(row.content)
                    break
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
        await TokenQuotaService(self.db).assert_under_daily_quota(user_id)
        if not regenerate:
            assert_chat_content_length(content)
            run_user_input_guards(content)
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

    async def _iter_runner_events_with_disconnect(
        self,
        state: ChatState,
        *,
        conversation_id: uuid.UUID,
        stream_id: str,
        request: Request | None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        """Delegate to runner stream_events; raise when HTTP client disconnects."""
        async for event in self.runner.stream_events(
            state,
            thread_id=str(conversation_id),
            db=self.db,
            request=request,
            stream_id=stream_id,
            cancel_cache=self.cancel_cache,
        ):
            yield event

        if request is not None and await request.is_disconnected():
            raise _ClientDisconnected

    @staticmethod
    def _truncate_tool_summary(summary: str) -> str:
        text = summary.strip()
        if len(text) <= TOOL_STEP_SUMMARY_MAX_LEN:
            return text
        return f"{text[:TOOL_STEP_SUMMARY_MAX_LEN]}…"

    @classmethod
    def _merge_tool_step(
        cls,
        pending: dict[str, Any],
        result_data: dict[str, Any],
    ) -> dict[str, Any]:
        step: dict[str, Any] = {
            "id": str(result_data.get("id") or pending.get("id") or ""),
            "name": str(result_data.get("name") or pending.get("name") or ""),
            "arguments": pending.get("arguments") or {},
            "success": bool(result_data.get("success", False)),
            "summary": cls._truncate_tool_summary(str(result_data.get("summary") or "")),
        }
        duration_ms = result_data.get("duration_ms")
        if isinstance(duration_ms, int):
            step["duration_ms"] = duration_ms
        return step

    def _maybe_emit_sources(
        self,
        stream_state: CompletionStreamState,
        *,
        sources_emitted: bool,
    ) -> tuple[dict | None, bool]:
        if sources_emitted:
            return None, True
        source_items = ChatGraphRunner.format_rag_source_items(
            self.runner.last_retrieved_chunks,
        )
        if source_items:
            stream_state.rag_source_items = source_items
            return {"event": "sources", "data": {"items": source_items}}, True
        return None, True

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
        conversation = await self.conversations.get_owned_conversation(
            stream_state.conversation_id,
            stream_state.user_id,
        )
        graph_state = self._to_graph_state(
            stream_state.user_id,
            history,
            context_summary=conversation.context_summary,
        )

        await self.cancel_cache.register_active(
            stream_state.stream_id,
            stream_state.conversation_id,
            stream_state.user_id,
        )
        yield {"event": "start", "data": {"stream_id": stream_state.stream_id}}

        sources_emitted = False
        pending_tool_calls: dict[str, dict[str, Any]] = {}

        try:
            async for event in self._iter_runner_events_with_disconnect(
                graph_state,
                conversation_id=stream_state.conversation_id,
                stream_id=stream_state.stream_id,
                request=request,
            ):
                sources_frame, sources_emitted = self._maybe_emit_sources(
                    stream_state,
                    sources_emitted=sources_emitted,
                )
                if sources_frame is not None:
                    yield sources_frame

                event_type = event.get("type")
                if event_type == "tool_call":
                    data = event["data"]
                    call_id = str(data.get("id") or "")
                    if call_id:
                        pending_tool_calls[call_id] = {
                            "id": call_id,
                            "name": data.get("name"),
                            "arguments": data.get("arguments") or {},
                        }
                    yield {"event": "tool_call", "data": data}
                    continue

                if event_type == "tool_result":
                    data = event["data"]
                    call_id = str(data.get("id") or "")
                    pending = pending_tool_calls.pop(call_id, {})
                    stream_state.tool_steps.append(
                        self._merge_tool_step(pending, data),
                    )
                    yield {"event": "tool_result", "data": data}
                    continue

                if event_type != "token":
                    logger.warning("ignoring unknown runner stream event: %r", event_type)
                    continue

                token = event.get("content")
                if not token:
                    continue
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
        stream_state.usage = self.runner.last_completion_usage

    async def _maybe_schedule_summary_background(
        self,
        conversation_id: uuid.UUID,
        background_tasks: BackgroundTasks | None,
    ) -> None:
        conversation = await self.conversations.conversations.get_by_id(
            conversation_id,
        )
        if conversation is None:
            return

        messages = await self.messages.list_by_conversation_id(conversation_id)
        decision = should_schedule_summary(conversation, messages)
        if not decision.should_schedule:
            return

        if background_tasks is None:
            logger.warning(
                "summary scheduled but BackgroundTasks missing conversation_id=%s",
                conversation_id,
            )
            return

        background_tasks.add_task(run_summary_background, conversation_id)

    def _maybe_schedule_memory_extract_background(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        background_tasks: BackgroundTasks | None,
    ) -> None:
        if not settings.memory_enabled or not settings.memory_long_term_enabled:
            return

        if background_tasks is None:
            logger.warning(
                "memory extract scheduled but BackgroundTasks missing conversation_id=%s",
                conversation_id,
            )
            return

        background_tasks.add_task(run_extract_background, conversation_id, user_id)

    async def _record_completion_usage_for_turn(
        self,
        stream_state: CompletionStreamState,
        *,
        message_id: uuid.UUID | None = None,
    ) -> None:
        if stream_state.usage_recorded or stream_state.usage is None:
            return
        await record_completion_usage_safe(
            self.db,
            user_id=stream_state.user_id,
            conversation_id=stream_state.conversation_id,
            usage=stream_state.usage,
            message_id=message_id,
        )
        stream_state.usage_recorded = True

    async def finalize_completion_stream(
        self,
        stream_state: CompletionStreamState,
        *,
        background_tasks: BackgroundTasks | None = None,
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
        if stream_state.persisted:
            return None

        assistant_id: uuid.UUID | None = None
        completion_status = COMPLETION_INTERRUPTED

        if not stream_state.terminal_error:
            has_assistant_text = bool(stream_state.assistant_parts)
            has_tool_steps = bool(stream_state.tool_steps)
            if has_assistant_text or has_tool_steps:
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
                if content or has_tool_steps:
                    assistant = await self.messages.create(
                        stream_state.conversation_id,
                        "assistant",
                        content,
                        completion_status=completion_status,
                    )
                    assistant_id = assistant.id
                    metadata: dict[str, Any] = {}
                    if stream_state.rag_source_items:
                        metadata["rag_sources"] = stream_state.rag_source_items
                    if stream_state.tool_steps:
                        metadata["tool_steps"] = stream_state.tool_steps
                    if metadata:
                        assistant.metadata_ = metadata

        await self._record_completion_usage_for_turn(
            stream_state,
            message_id=assistant_id,
        )

        if assistant_id is None and not stream_state.usage_recorded:
            return None

        if assistant_id is not None:
            await self.conversations.touch_activity(stream_state.conversation_id)
        await self.db.commit()
        await self.conversations.invalidate_list_cache(stream_state.user_id)
        stream_state.persisted = True
        if (
            assistant_id is not None
            and completion_status == COMPLETION_COMPLETE
        ):
            self._maybe_schedule_memory_extract_background(
                stream_state.conversation_id,
                stream_state.user_id,
                background_tasks,
            )
            await self._maybe_schedule_summary_background(
                stream_state.conversation_id,
                background_tasks,
            )
        return assistant_id
