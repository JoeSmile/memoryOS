from typing import Any

import httpx

from app.core.config import settings
from app.services.security.content_provenance import (
    ContentProvenance,
    shield_text_for_provenance,
)
from app.tools.definitions import ToolContext, ToolDefinition
from app.tools.registry import ToolRegistry

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
_SNIPPET_MAX_LEN = 240

TAVILY_SEARCH_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Web search query when knowledge retrieval is insufficient.",
        },
    },
    "required": ["query"],
}

_MOCK_RESULTS: list[dict[str, str]] = [
    {
        "title": "Mock web result (TAVILY_API_KEY unset)",
        "url": "https://example.com/mock-tavily",
        "snippet": "Deterministic harness snippet for offline agent tool tests.",
    },
]


async def tavily_search_handler(
    arguments: dict[str, Any],
    _context: ToolContext,
) -> dict[str, Any]:
    query = str(arguments.get("query", "")).strip()
    if not query:
        raise ValueError("query must be a non-empty string")

    if settings.use_mock_tavily:
        return _mock_response(query)

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": settings.tavily_max_results,
        "search_depth": "basic",
    }
    async with httpx.AsyncClient(timeout=settings.agent_tool_timeout_seconds) as client:
        response = await client.post(TAVILY_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()

    return _format_tavily_response(query, data)


def build_tavily_search_tool() -> ToolDefinition:
    return ToolDefinition(
        name="tavily_search",
        description=(
            "Search the public web for up-to-date information. "
            "Use when retrieved knowledge does not answer the user's question—"
            "e.g. wrong year, stale corpus, or missing entities—or when the question "
            "requires current events not in the knowledge base."
        ),
        parameters=TAVILY_SEARCH_PARAMETERS,
        handler=tavily_search_handler,
    )


def register_tavily_search(registry: ToolRegistry) -> None:
    registry.register(build_tavily_search_tool())


def _mock_response(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "results": [
            {
                "title": item["title"],
                "url": item["url"],
                "snippet": shield_text_for_provenance(
                    item["snippet"],
                    ContentProvenance.WEB_SEARCH,
                ),
            }
            for item in _MOCK_RESULTS
        ],
        "mock": True,
    }


def _format_tavily_response(query: str, data: dict[str, Any]) -> dict[str, Any]:
    raw_results = data.get("results")
    if not isinstance(raw_results, list):
        raw_results = []

    results: list[dict[str, str]] = []
    for item in raw_results[: settings.tavily_max_results]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        content = str(item.get("content") or item.get("snippet") or "").strip()
        snippet = content
        if len(snippet) > _SNIPPET_MAX_LEN:
            snippet = f"{snippet[:_SNIPPET_MAX_LEN]}…"
        snippet = shield_text_for_provenance(snippet, ContentProvenance.WEB_SEARCH)
        if not title and not url and not snippet:
            continue
        results.append({"title": title, "url": url, "snippet": snippet})

    return {"query": query, "results": results}
