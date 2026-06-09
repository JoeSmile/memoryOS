"""ReAct tool execution and conditional routing (EP05)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from app.graphs.chat_state import ChatState
from app.tools import ToolContext, build_tool_executor

logger = logging.getLogger(__name__)

Route = Literal["execute_tools"] | str


def should_continue(state: ChatState) -> Route:
    """Continue the ReAct loop when the latest assistant turn requested tools."""
    messages = state.get("messages") or []
    if not messages:
        return END

    last = messages[-1]
    if not isinstance(last, AIMessage):
        return END

    tool_calls = getattr(last, "tool_calls", None) or []
    if tool_calls:
        return "execute_tools"
    return END


def _parse_tool_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def _error_tool_content(error: str) -> str:
    return json.dumps(
        {"success": False, "summary": error, "error": error},
        ensure_ascii=False,
    )


def _tool_result_content(result: Any) -> str:
    payload: dict[str, Any] = {
        "success": result.success,
        "summary": result.summary,
    }
    if result.success:
        payload["output"] = result.output
    elif result.error:
        payload["error"] = result.error
    return json.dumps(payload, ensure_ascii=False, default=str)


def _tool_call_fields(call: Any) -> tuple[str, str, dict[str, Any]]:
    if isinstance(call, dict):
        return (
            str(call.get("name") or ""),
            str(call.get("id") or ""),
            _parse_tool_arguments(call.get("args")),
        )
    return (
        str(getattr(call, "name", "") or ""),
        str(getattr(call, "id", "") or ""),
        _parse_tool_arguments(getattr(call, "args", {})),
    )


async def execute_tools(state: ChatState, config: RunnableConfig) -> dict:
    """Run model-requested tools and append ToolMessage results for the next turn."""
    messages = state.get("messages") or []
    if not messages:
        return {}

    last = messages[-1]
    if not isinstance(last, AIMessage):
        return {}

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return {}

    configurable = config.get("configurable") or {}
    db = configurable.get("db")
    user_id = state.get("user_id", "")

    executor = build_tool_executor()
    tool_messages: list[ToolMessage] = []

    for index, call in enumerate(tool_calls):
        name, tool_call_id, arguments = _tool_call_fields(call)
        if not tool_call_id:
            tool_call_id = f"malformed_{index}"
            logger.warning("tool call missing id, using placeholder: %r", call)

        if not name:
            logger.warning("malformed tool call missing name: %r", call)
            tool_messages.append(
                ToolMessage(
                    content=_error_tool_content("malformed_tool_call: missing tool name"),
                    tool_call_id=tool_call_id,
                    name="unknown",
                )
            )
            continue

        result = await executor.run(
            name,
            arguments,
            ToolContext(user_id=user_id, db=db),
        )
        tool_messages.append(
            ToolMessage(
                content=_tool_result_content(result),
                tool_call_id=tool_call_id,
                name=name,
            )
        )

    return {"messages": tool_messages}
