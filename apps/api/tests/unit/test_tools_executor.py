import asyncio

import pytest

from app.tools import ToolContext, ToolDefinition, ToolExecutor, ToolRegistry


async def _echo_handler(args: dict, _context: ToolContext) -> dict:
    return {"query": args["query"]}


def _echo_tool() -> ToolDefinition:
    return ToolDefinition(
        name="echo",
        description="echo query",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        handler=_echo_handler,
    )


@pytest.mark.asyncio
async def test_executor_runs_registered_tool():
    registry = ToolRegistry()
    registry.register(_echo_tool())
    executor = ToolExecutor(registry)
    result = await executor.run(
        "echo",
        {"query": "hello"},
        ToolContext(user_id="user-1"),
    )
    assert result.success is True
    assert result.output == {"query": "hello"}


@pytest.mark.asyncio
async def test_executor_rejects_unknown_tool():
    executor = ToolExecutor(ToolRegistry())
    result = await executor.run(
        "missing",
        {},
        ToolContext(user_id="user-1"),
    )
    assert result.success is False
    assert "unknown_tool" in (result.error or "")


@pytest.mark.asyncio
async def test_executor_rejects_invalid_arguments():
    registry = ToolRegistry()
    registry.register(_echo_tool())
    executor = ToolExecutor(registry)
    result = await executor.run("echo", {}, ToolContext(user_id="user-1"))
    assert result.success is False
    assert "invalid_arguments" in (result.error or "")


@pytest.mark.asyncio
async def test_executor_rejects_bool_as_integer():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="count",
            description="count items",
            parameters={
                "type": "object",
                "properties": {"n": {"type": "integer"}},
                "required": ["n"],
            },
            handler=_echo_handler,
        ),
    )
    executor = ToolExecutor(registry)
    result = await executor.run("count", {"n": True}, ToolContext(user_id="user-1"))
    assert result.success is False
    assert "invalid_arguments" in (result.error or "")


@pytest.mark.asyncio
async def test_executor_handler_exception_becomes_failure():
    async def _boom(_args: dict, _context: ToolContext) -> None:
        raise RuntimeError("boom")

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="boom",
            description="always fails",
            parameters={"type": "object", "properties": {}},
            handler=_boom,
        ),
    )
    executor = ToolExecutor(registry)
    result = await executor.run("boom", {}, ToolContext(user_id="user-1"))
    assert result.success is False
    assert "tool_error" in (result.error or "")
    assert "boom" in (result.summary or "")


@pytest.mark.asyncio
async def test_executor_timeout_becomes_failure():
    async def _slow(_args: dict, _context: ToolContext) -> str:
        await asyncio.sleep(0.05)
        return "late"

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="slow",
            description="slow tool",
            parameters={"type": "object", "properties": {}},
            handler=_slow,
        ),
    )
    executor = ToolExecutor(registry, timeout_seconds=0.01)
    result = await executor.run("slow", {}, ToolContext(user_id="user-1"))
    assert result.success is False
    assert "tool_timeout" in (result.error or "")
