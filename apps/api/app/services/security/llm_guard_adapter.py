"""Optional LLM Guard adapter for user-input scanning (EP09 2.9)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

ScanPromptFn = Callable[[list[Any], str], tuple[str, list[bool], list[float]]]

_scanners: list[Any] | None = None
_scan_prompt: ScanPromptFn | None = None
_import_failed = False


def _ensure_llm_guard() -> tuple[list[Any], ScanPromptFn] | None:
    global _scanners, _scan_prompt, _import_failed
    if _import_failed:
        return None
    if _scanners is not None and _scan_prompt is not None:
        return _scanners, _scan_prompt
    try:
        from llm_guard import scan_prompt
        from llm_guard.input_scanners import InvisibleText, PromptInjection
    except ImportError:
        _import_failed = True
        logger.warning(
            "LLM_GUARD_ENABLED but llm-guard is not installed; skipping ML input scan",
        )
        return None

    _scanners = [
        InvisibleText(),
        PromptInjection(threshold=settings.llm_guard_prompt_injection_threshold),
    ]
    _scan_prompt = scan_prompt
    return _scanners, _scan_prompt


def assert_llm_guard_user_input(content: str) -> None:
    """Scan user text with LLM Guard when enabled; no-op when off or package missing."""
    if not settings.llm_guard_enabled:
        return

    loaded = _ensure_llm_guard()
    if loaded is None:
        return

    scanners, scan_prompt = loaded
    started = time.perf_counter()
    _sanitized, results_valid, _results_score = scan_prompt(scanners, content)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("llm_guard user-input scan %.1fms valid=%s", elapsed_ms, results_valid)

    if not all(results_valid):
        raise AppException(
            code=42201,
            message="prompt_injection_detected",
            status_code=422,
        )
