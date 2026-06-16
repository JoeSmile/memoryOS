"""Optional EntropyShield DeSyntax for untrusted content (EP09 2.10)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.core.config import settings
from app.services.security.content_provenance import ContentProvenance

logger = logging.getLogger(__name__)

ShieldFn = Callable[[str], str]
ShieldWithStatsFn = Callable[..., dict[str, Any]]

_shield: ShieldFn | None = None
_shield_with_stats: ShieldWithStatsFn | None = None
_import_failed = False


def _ensure_entropyshield() -> ShieldFn | None:
    global _shield, _shield_with_stats, _import_failed
    if _import_failed:
        return None
    if _shield is not None:
        return _shield
    try:
        from entropyshield import shield, shield_with_stats
    except ImportError:
        _import_failed = True
        logger.warning(
            "ENTROPYSHIELD_ENABLED but entropyshield is not installed; "
            "skipping DeSyntax mask on untrusted content",
        )
        return None

    _shield = shield
    _shield_with_stats = shield_with_stats
    return _shield


def apply_entropyshield(
    text: str,
    *,
    provenance: ContentProvenance,
) -> str:
    """Stride-mask untrusted text when master switch is on; no-op when off or package missing."""
    if not settings.entropyshield_enabled:
        return text

    if _ensure_entropyshield() is None:
        return text

    started = time.perf_counter()
    if _shield_with_stats is not None:
        result = _shield_with_stats(text)
        masked = str(result["masked_text"])
        stats = result.get("stats", {})
        visible = int(stats.get("visible", 0))
        total = int(stats.get("total", 0))
        visible_ratio = visible / total if total else 1.0
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "entropyshield %s %.1fms visible_ratio=%.2f chars=%d",
            provenance.value,
            elapsed_ms,
            visible_ratio,
            total,
        )
        return masked

    assert _shield is not None
    return _shield(text)
