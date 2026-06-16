"""Optional llm-injection-guard adapter for HTTP / compare with heuristic 2.2 (EP09 2.11)."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

_scanner: Any | None = None
_injection_detected_error: type[BaseException] | None = None
_import_failed = False


def _ensure_prompt_scanner() -> Any | None:
    global _scanner, _injection_detected_error, _import_failed
    if _import_failed:
        return None
    if _scanner is not None:
        return _scanner
    try:
        from llm_injection_guard import PromptScanner
        from llm_injection_guard.exceptions import InjectionDetectedError
    except ImportError:
        _import_failed = True
        logger.warning(
            "LLM_INJECTION_GUARD_ENABLED but llm-injection-guard is not installed; "
            "skipping middleware scan",
        )
        return None

    _injection_detected_error = InjectionDetectedError
    _scanner = PromptScanner(
        threshold_score=settings.llm_injection_guard_threshold_score,
        block_on_detection=True,
    )
    return _scanner


def _is_injection_detected(exc: BaseException) -> bool:
    if _injection_detected_error is not None and isinstance(exc, _injection_detected_error):
        return True
    return type(exc).__name__ == "InjectionDetectedError"


def assert_llm_injection_guard_user_input(content: str) -> None:
    """Scan user text with llm-injection-guard when enabled; no-op when off or package missing."""
    if not settings.llm_injection_guard_enabled:
        return

    scanner = _ensure_prompt_scanner()
    if scanner is None:
        return

    started = time.perf_counter()
    try:
        scanner.scan(content)
    except Exception as exc:
        if not _is_injection_detected(exc):
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "llm_injection_guard blocked %.1fms level=%s",
            elapsed_ms,
            getattr(exc, "threat_level", "unknown"),
        )
        raise AppException(
            code=42201,
            message="prompt_injection_detected",
            status_code=422,
        ) from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("llm_injection_guard user-input scan %.1fms allow", elapsed_ms)
