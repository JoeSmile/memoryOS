from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graphs.chat_state import ChatState
from app.graphs.nodes.call_model import call_model


@lru_cache
def build_chat_graph():
    """Compiled graph: START -> call_model -> END."""
    builder = StateGraph(ChatState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    builder.add_edge("call_model", END)
    return builder.compile()
