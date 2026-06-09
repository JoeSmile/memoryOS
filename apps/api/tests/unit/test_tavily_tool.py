import pytest

from app.tools import ToolContext, ToolExecutor, ToolRegistry, build_tool_registry
from app.tools.builtin.tavily_search import (
    _format_tavily_response,
    build_tavily_search_tool,
)


@pytest.mark.asyncio
async def test_tavily_search_mock_without_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.tools.builtin.tavily_search.settings.tavily_api_key",
        None,
    )
    registry = ToolRegistry()
    registry.register(build_tavily_search_tool())
    executor = ToolExecutor(registry)

    result = await executor.run(
        "tavily_search",
        {"query": "2026 world cup host"},
        ToolContext(user_id="user-1"),
    )

    assert result.success is True
    assert result.output is not None
    assert result.output["mock"] is True
    assert len(result.output["results"]) >= 1


@pytest.mark.asyncio
async def test_tavily_search_rejects_empty_query(monkeypatch):
    monkeypatch.setattr(
        "app.tools.builtin.tavily_search.settings.tavily_api_key",
        None,
    )
    registry = ToolRegistry()
    registry.register(build_tavily_search_tool())
    executor = ToolExecutor(registry)

    result = await executor.run(
        "tavily_search",
        {"query": "   "},
        ToolContext(user_id="user-1"),
    )

    assert result.success is False
    assert "tool_error" in (result.error or "")


def test_build_tool_registry_includes_tavily():
    registry = build_tool_registry()
    schemas = registry.list_openai_schemas()
    assert any(item["function"]["name"] == "tavily_search" for item in schemas)


def test_format_tavily_response_truncates_snippet():
    long_content = "x" * 300
    formatted = _format_tavily_response(
        "q",
        {"results": [{"title": "t", "url": "https://example.com", "content": long_content}]},
    )
    assert formatted["results"][0]["snippet"].endswith("…")
    assert len(formatted["results"][0]["snippet"]) <= 241
