"""Redis cache for embedding vectors (EP09 Story 9.2)."""

from __future__ import annotations

import hashlib
import json
import logging

from redis.asyncio import Redis

from app.cache.keys import embedding_vector_key
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def normalize_embedding_text(text: str) -> str:
    """Stable cache key input: trim and collapse whitespace."""
    return " ".join(text.split())


def embedding_text_digest(text: str) -> str:
    normalized = normalize_embedding_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class EmbeddingCache:
    def __init__(
        self,
        redis: Redis | None,
        settings: Settings | None = None,
    ) -> None:
        self.redis = redis
        self._settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.redis is not None and self._settings.embedding_cache_enabled

    @property
    def ttl(self) -> int:
        return self._settings.embedding_cache_ttl_seconds

    def _key(self, *, model_label: str, dimensions: int, text: str) -> str:
        return embedding_vector_key(
            model_label=model_label,
            dimensions=dimensions,
            text_digest=embedding_text_digest(text),
        )

    async def get_vector(
        self,
        *,
        model_label: str,
        dimensions: int,
        text: str,
    ) -> list[float] | None:
        if not self.enabled:
            return None
        try:
            raw = await self.redis.get(  # type: ignore[union-attr]
                self._key(model_label=model_label, dimensions=dimensions, text=text),
            )
            if raw is None:
                return None
            parsed = json.loads(raw)
            if not isinstance(parsed, list) or len(parsed) != dimensions:
                return None
            return [float(value) for value in parsed]
        except Exception:
            logger.debug("embedding cache get failed", exc_info=True)
            return None

    async def set_vector(
        self,
        *,
        model_label: str,
        dimensions: int,
        text: str,
        vector: list[float],
    ) -> None:
        if not self.enabled:
            return
        if len(vector) != dimensions:
            return
        try:
            await self.redis.setex(  # type: ignore[union-attr]
                self._key(model_label=model_label, dimensions=dimensions, text=text),
                self.ttl,
                json.dumps(vector),
            )
        except Exception:
            logger.debug("embedding cache set failed", exc_info=True)
