import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

from starlette.requests import Request

from app.cache.stream_cancel_cache import StreamCancelCache
from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.chat_state import ChatState
from app.graphs.nodes import mock_model

_DISCONNECT_POLL_SECONDS = 0.25


class ChatGraphRunner:
    """Stream text tokens from the chat graph for SSE (ep02-chat-sse)."""

    def __init__(self, graph: Any | None = None) -> None:
        self._graph = graph if graph is not None else build_chat_graph()

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

    async def _iter_source_tokens(
        self,
        state: ChatState,
        *,
        thread_id: str | None,
    ) -> AsyncIterator[str]:
        if settings.use_mock_llm:
            async for token in mock_model.mock_stream_tokens():
                yield token
            return

        config: dict[str, Any] = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        async with contextlib.aclosing(
            self._graph.astream_events(state, config=config, version="v2")
        ) as event_stream:
            async for event in event_stream:
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
        request: Request | None = None,
        stream_id: str | None = None,
        cancel_cache: StreamCancelCache | None = None,
    ) -> AsyncIterator[str]:
        agen = self._iter_source_tokens(state, thread_id=thread_id).__aiter__()
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
