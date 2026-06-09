from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict


class ChatState(TypedDict):
    """LangGraph state for EP02 chat + EP04 RAG retrieve + EP05 ReAct."""

    messages: Annotated[list, add_messages]
    user_id: str
    retrieved_chunks: NotRequired[list[dict[str, Any]]]
    rag_sufficient: NotRequired[bool]
