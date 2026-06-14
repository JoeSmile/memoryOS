import asyncio
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any, Literal, TypedDict

from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.cache.stream_cancel_cache import StreamCancelCache
from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.chat_state import ChatState
from app.graphs.nodes import mock_model
from app.graphs.nodes.retrieve import retrieve_knowledge

_DISCONNECT_POLL_SECONDS = 0.25


_CONTENT_PREVIEW_MAX_LEN = 240


class TokenStreamEvent(TypedDict):
    type: Literal["token"]
    content: str


class ToolCallStreamEvent(TypedDict):
    type: Literal["tool_call"]
    data: dict[str, Any]


class ToolResultStreamEvent(TypedDict):
    type: Literal["tool_result"]
    data: dict[str, Any]


RunnerStreamEvent = TokenStreamEvent | ToolCallStreamEvent | ToolResultStreamEvent


def _format_tool_call(call: Any) -> dict[str, Any]:
    if isinstance(call, dict):
        return {
            "id": call.get("id"),
            "name": call.get("name"),
            "arguments": call.get("args") or {},
        }
    return {
        "id": getattr(call, "id", None),
        "name": getattr(call, "name", None),
        "arguments": getattr(call, "args", {}) or {},
    }


def _format_tool_result(message: ToolMessage) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": message.tool_call_id,
        "name": message.name,
    }
    try:
        payload = json.loads(message.content)
        if isinstance(payload, dict):
            data["success"] = bool(payload.get("success", False))
            data["summary"] = payload.get("summary", "")
            duration_ms = payload.get("duration_ms")
            if isinstance(duration_ms, int):
                data["duration_ms"] = duration_ms
            if payload.get("error"):
                data["error"] = payload["error"]
            return data
    except json.JSONDecodeError:
        pass
    data["success"] = False
    data["summary"] = message.content
    return data


def _text_content(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content) if content else ""


def _chunk_content_for_stream(text: str) -> list[str]:
    if text == mock_model.MOCK_ASSISTANT_TEXT:
        return list(mock_model.MOCK_TOKEN_CHUNKS)
    if text == mock_model.MOCK_AFTER_TOOL_TEXT:
        return list(mock_model.MOCK_AFTER_TOOL_CHUNKS)
    return list(text) if text else []


def _events_from_call_model_output(output: dict[str, Any]) -> list[RunnerStreamEvent]:
    events: list[RunnerStreamEvent] = []
    messages = output.get("messages") or []
    for message in messages:
        if not isinstance(message, AIMessage):
            continue
        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            for call in tool_calls:
                events.append({"type": "tool_call", "data": _format_tool_call(call)})
            continue
        text = _text_content(message)
        for chunk in _chunk_content_for_stream(text):
            events.append({"type": "token", "content": chunk})
    return events


def _events_from_execute_tools_output(output: dict[str, Any]) -> list[RunnerStreamEvent]:
    events: list[RunnerStreamEvent] = []
    for message in output.get("messages") or []:
        if isinstance(message, ToolMessage):
            events.append({"type": "tool_result", "data": _format_tool_result(message)})
    return events


class ChatGraphRunner:
    """Stream graph output as SSE-ready events (tokens + ReAct tool rounds)."""

    def __init__(self, graph: Any | None = None) -> None:
        self._graph = graph if graph is not None else build_chat_graph()
        self._last_retrieved_chunks: list[dict[str, Any]] = []

    @property
    def last_retrieved_chunks(self) -> list[dict[str, Any]]:
        """Chunks from the latest retrieve pass (for RAG sources SSE in task 4.1)."""
        return self._last_retrieved_chunks

    @staticmethod
    def format_rag_source_items(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map retrieve node payloads to chat SSE `sources.data.items` shape."""
        items: list[dict[str, Any]] = []
        for chunk in chunks:
            content = chunk.get("content")
            preview = ""
            if isinstance(content, str):
                text = content.strip()
                if len(text) > _CONTENT_PREVIEW_MAX_LEN:
                    preview = f"{text[:_CONTENT_PREVIEW_MAX_LEN]}…"
                else:
                    preview = text
            items.append(
                {
                    "external_id": chunk.get("external_id"),
                    "collection": chunk.get("collection"),
                    "entity_type": chunk.get("entity_type"),
                    "score": chunk.get("score"),
                    "content_preview": preview,
                }
            )
        return items

    @staticmethod
    async def _should_stop(
        *,
        request: Request | None,
        stream_id: str | None,
        cancel_cache: StreamCancelCache | None,
    ) -> bool:
        if request is not None and await request.is_disconnected():
            return True
        if stream_id is not None and cancel_cache is not None:
            return await cancel_cache.is_cancelled(stream_id)
        return False

    @staticmethod
    def _graph_config(
        *,
        db: AsyncSession | None,
        thread_id: str | None,
    ) -> dict[str, Any]:
        configurable: dict[str, Any] = {}
        if db is not None:
            configurable["db"] = db
        if thread_id:
            configurable["thread_id"] = thread_id
        return {"configurable": configurable} if configurable else {}

    def _run_config(
        self,
        *,
        db: AsyncSession | None,
        thread_id: str | None,
    ) -> dict[str, Any]:
        config = self._graph_config(db=db, thread_id=thread_id)
        if settings.agent_tools_enabled:
            recursion_limit = settings.agent_max_iterations
            if settings.memory_enabled:
                # EP06 prep nodes (trim_history, load_user_memories) precede retrieve.
                recursion_limit += 2
            config = {
                **config,
                "recursion_limit": recursion_limit,
            }
        return config

    async def _retrieve_for_mock_stream(
        self,
        state: ChatState,
        *,
        db: AsyncSession | None,
    ) -> None:
        self._last_retrieved_chunks = []
        if not settings.rag_chat_enabled or db is None:
            return
        update = await retrieve_knowledge(
            state,
            self._graph_config(db=db, thread_id=None),
        )
        self._last_retrieved_chunks = update.get("retrieved_chunks") or []

    async def _iter_legacy_mock_tokens(
        self,
        state: ChatState,
        *,
        db: AsyncSession | None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        """EP04 mock path when AGENT_TOOLS_ENABLED=false."""
        await self._retrieve_for_mock_stream(state, db=db)
        async for token in mock_model.mock_stream_tokens():
            yield {"type": "token", "content": token}

    async def _iter_graph_stream_events(
        self,
        state: ChatState,
        *,
        thread_id: str | None,
        db: AsyncSession | None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        self._last_retrieved_chunks = []
        config = self._run_config(db=db, thread_id=thread_id)

        async with contextlib.aclosing(
            self._graph.astream_events(state, config=config, version="v2")
        ) as event_stream:
            async for event in event_stream:
                if event.get("event") == "on_chain_end":
                    node_name = event.get("name")
                    output = event.get("data", {}).get("output") or {}
                    if not isinstance(output, dict):
                        continue
                    if node_name == "retrieve_knowledge":
                        self._last_retrieved_chunks = output.get("retrieved_chunks") or []
                        continue
                    if node_name == "call_model" and settings.agent_tools_enabled:
                        for item in _events_from_call_model_output(output):
                            yield item
                        continue
                    if node_name == "execute_tools":
                        for item in _events_from_execute_tools_output(output):
                            yield item
                    continue

                if settings.agent_tools_enabled:
                    continue

                if event.get("event") != "on_chat_model_stream":
                    continue
                chunk = event.get("data", {}).get("chunk")
                if chunk is None:
                    continue
                content = getattr(chunk, "content", None)
                if content:
                    yield {"type": "token", "content": content}

    async def _iter_stream_events(
        self,
        state: ChatState,
        *,
        thread_id: str | None,
        db: AsyncSession | None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        if settings.use_mock_llm and not settings.agent_tools_enabled:
            async for event in self._iter_legacy_mock_tokens(state, db=db):
                yield event
            return

        async for event in self._iter_graph_stream_events(
            state,
            thread_id=thread_id,
            db=db,
        ):
            yield event

    async def _stream_with_cancel(
        self,
        agen: AsyncIterator[RunnerStreamEvent],
        *,
        request: Request | None,
        stream_id: str | None,
        cancel_cache: StreamCancelCache | None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        iterator = agen.__aiter__()
        pending: asyncio.Task[RunnerStreamEvent] | None = None
        try:
            pending = asyncio.create_task(iterator.__anext__())
            while pending is not None:
                if await self._should_stop(
                    request=request,
                    stream_id=stream_id,
                    cancel_cache=cancel_cache,
                ):
                    return

                done, _ = await asyncio.wait(
                    {pending},
                    timeout=_DISCONNECT_POLL_SECONDS,
                )
                if pending in done:
                    try:
                        yield pending.result()
                    except StopAsyncIteration:
                        return
                    pending = asyncio.create_task(iterator.__anext__())
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await pending
            with contextlib.suppress(Exception):
                await agen.aclose()

    async def stream_events(
        self,
        state: ChatState,
        *,
        thread_id: str | None = None,
        db: AsyncSession | None = None,
        request: Request | None = None,
        stream_id: str | None = None,
        cancel_cache: StreamCancelCache | None = None,
    ) -> AsyncIterator[RunnerStreamEvent]:
        agen = self._iter_stream_events(
            state,
            thread_id=thread_id,
            db=db,
        )
        async for event in self._stream_with_cancel(
            agen,
            request=request,
            stream_id=stream_id,
            cancel_cache=cancel_cache,
        ):
            yield event

    async def stream_tokens(
        self,
        state: ChatState,
        *,
        thread_id: str | None = None,
        db: AsyncSession | None = None,
        request: Request | None = None,
        stream_id: str | None = None,
        cancel_cache: StreamCancelCache | None = None,
    ) -> AsyncIterator[str]:
        async for event in self.stream_events(
            state,
            thread_id=thread_id,
            db=db,
            request=request,
            stream_id=stream_id,
            cancel_cache=cancel_cache,
        ):
            if event["type"] == "token":
                yield event["content"]
