from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graphs.chat_state import ChatState
from app.graphs.nodes.call_model import call_model
from app.graphs.nodes.retrieve import retrieve_knowledge


@lru_cache
def build_chat_graph():
    """Compiled graph: START -> retrieve_knowledge -> call_model -> END."""
    builder = StateGraph(ChatState)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "call_model")
    builder.add_edge("call_model", END)
    return builder.compile()
