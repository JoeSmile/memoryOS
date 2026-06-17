"""Collect LLM token usage from graph nodes (LangGraph strips usage from stream events)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from app.services.token_quota_service import TokenUsageSnapshot

UsageCollector = Callable[[TokenUsageSnapshot], None]

# LangGraph may run node bodies and stream callbacks on different tasks, so
# ContextVar is unreliable here. Pending usage is FIFO per worker process.
_pending_round_usage: deque[TokenUsageSnapshot] = deque()


def get_usage_collector(configurable: dict[str, Any] | None) -> UsageCollector | None:
    if not configurable:
        return None
    collector = configurable.get("usage_collector")
    if callable(collector):
        return collector
    return None


def stage_current_round_usage(usage: TokenUsageSnapshot | None) -> None:
    if usage is not None:
        _pending_round_usage.append(usage)


def take_current_round_usage() -> TokenUsageSnapshot | None:
    if not _pending_round_usage:
        return None
    return _pending_round_usage.popleft()


def reset_pending_round_usage() -> None:
    _pending_round_usage.clear()


def emit_usage(
    configurable: dict[str, Any] | None,
    usage: TokenUsageSnapshot | None,
) -> None:
    stage_current_round_usage(usage)
