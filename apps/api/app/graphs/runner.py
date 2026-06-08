import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

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


class ChatGraphRunner:
    """Stream text tokens from the chat graph for SSE (ep02-chat-sse)."""

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

    async def _iter_source_tokens(
        self,
        state: ChatState,
        *,
        thread_id: str | None,
        db: AsyncSession | None,
    ) -> AsyncIterator[str]:
        if settings.use_mock_llm:
            await self._retrieve_for_mock_stream(state, db=db)
            async for token in mock_model.mock_stream_tokens():
                yield token
            return

        self._last_retrieved_chunks = []
        config = self._graph_config(db=db, thread_id=thread_id)

        async with contextlib.aclosing(
            self._graph.astream_events(state, config=config, version="v2")
        ) as event_stream:
            async for event in event_stream:
                if (
                    event.get("event") == "on_chain_end"
                    and event.get("name") == "retrieve_knowledge"
                ):
                    output = event.get("data", {}).get("output") or {}
                    self._last_retrieved_chunks = output.get("retrieved_chunks") or []
                if event.get("event") != "on_chat_model_stream":
                    continue
                chunk = event.get("data", {}).get("chunk")
                if chunk is None:
                    continue
                content = getattr(chunk, "content", None)
                if content:
                    yield content

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
        agen = self._iter_source_tokens(
            state,
            thread_id=thread_id,
            db=db,
        ).__aiter__()
        pending: asyncio.Task[str] | None = None
        try:
            pending = asyncio.create_task(agen.__anext__())
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
                    pending = asyncio.create_task(agen.__anext__())
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await pending
            with contextlib.suppress(Exception):
                await agen.aclose()
