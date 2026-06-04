from collections.abc import AsyncIterator
from typing import Any

from app.core.config import settings
from app.graphs.chat_graph import build_chat_graph
from app.graphs.chat_state import ChatState
from app.graphs.nodes.mock_model import mock_stream_tokens


class ChatGraphRunner:
    """Stream text tokens from the chat graph for SSE (ep02-chat-sse)."""

    def __init__(self, graph: Any | None = None) -> None:
        self._graph = graph if graph is not None else build_chat_graph()

    async def stream_tokens(
        self,
        state: ChatState,
        *,
        thread_id: str | None = None,
    ) -> AsyncIterator[str]:
        if settings.use_mock_llm:
            async for token in mock_stream_tokens():
                yield token
            return

        config: dict[str, Any] = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        async for event in self._graph.astream_events(
            state,
            config=config,
            version="v2",
        ):
            if event.get("event") != "on_chat_model_stream":
                continue
            chunk = event.get("data", {}).get("chunk")
            if chunk is None:
                continue
            content = getattr(chunk, "content", None)
            if content:
                yield content
