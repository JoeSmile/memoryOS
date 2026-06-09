import asyncio
import json
import logging
import time
from typing import Any

from app.tools.definitions import (
    ToolContext,
    ToolExecutionResult,
    validate_tool_arguments,
)
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 10.0
_SUMMARY_MAX_LEN = 512


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._registry = registry
        self._timeout_seconds = timeout_seconds

    async def run(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolExecutionResult:
        started = time.perf_counter()
        tool = self._registry.get(name)
        if tool is None:
            return self._failure(
                started=started,
                error=f"unknown_tool: {name}",
            )

        validation_error = validate_tool_arguments(arguments, tool.parameters)
        if validation_error is not None:
            return self._failure(
                started=started,
                error=f"invalid_arguments: {validation_error}",
            )

        try:
            output = await asyncio.wait_for(
                tool.handler(arguments, context),
                timeout=self._timeout_seconds,
            )
        except TimeoutError:
            return self._failure(started=started, error=f"tool_timeout: {name}")
        except Exception as exc:
            logger.warning("tool handler failed: %s", name, exc_info=exc)
            return self._failure(started=started, error=f"tool_error: {exc}")

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolExecutionResult(
            success=True,
            output=output,
            summary=_summarize_output(output),
            duration_ms=duration_ms,
        )

    @staticmethod
    def _failure(*, started: float, error: str) -> ToolExecutionResult:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolExecutionResult(
            success=False,
            output=None,
            summary=error,
            duration_ms=duration_ms,
            error=error,
        )


def _summarize_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        text = output.strip()
    else:
        try:
            text = json.dumps(output, ensure_ascii=False, default=str)
        except TypeError:
            text = str(output)
    if len(text) > _SUMMARY_MAX_LEN:
        return f"{text[:_SUMMARY_MAX_LEN]}…"
    return text
