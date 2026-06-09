from app.core.config import settings
from app.tools.builtin.tavily_search import register_tavily_search
from app.tools.definitions import (
    ToolContext,
    ToolDefinition,
    ToolExecutionResult,
)
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_tavily_search(registry)
    return registry


def build_tool_executor() -> ToolExecutor:
    return ToolExecutor(
        build_tool_registry(),
        timeout_seconds=settings.agent_tool_timeout_seconds,
    )


__all__ = [
    "ToolContext",
    "ToolDefinition",
    "ToolExecutionResult",
    "ToolExecutor",
    "ToolRegistry",
    "build_tool_executor",
    "build_tool_registry",
]
