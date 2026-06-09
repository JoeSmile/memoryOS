from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.nodes.call_model import call_model
from app.graphs.nodes.execute_tools import execute_tools, should_continue
from app.graphs.nodes.retrieve import retrieve_knowledge


def _build_rag_only_graph():
    """EP04: retrieve → call_model → END (no tool loop)."""
    builder = StateGraph(ChatState)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "call_model")
    builder.add_edge("call_model", END)
    return builder.compile()


def _build_react_graph():
    """EP05: retrieve → call_model ↔ execute_tools until no tool_calls."""
    builder = StateGraph(ChatState)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("call_model", call_model)
    builder.add_node("execute_tools", execute_tools)
    builder.add_edge(START, "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "call_model")
    builder.add_conditional_edges(
        "call_model",
        should_continue,
        ["execute_tools", END],
    )
    builder.add_edge("execute_tools", "call_model")
    return builder.compile()


@lru_cache
def build_chat_graph():
    """Compiled chat graph; ReAct loop when AGENT_TOOLS_ENABLED (default true)."""
    if settings.agent_tools_enabled:
        return _build_react_graph()
    return _build_rag_only_graph()
