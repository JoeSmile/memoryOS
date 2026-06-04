from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ChatState(TypedDict):
    """LangGraph state for EP02 minimal chat (messages + JWT user)."""

    messages: Annotated[list, add_messages]
    user_id: str
