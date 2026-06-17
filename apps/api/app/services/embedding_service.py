import hashlib
import math

from langchain_openai import OpenAIEmbeddings
from redis.asyncio import Redis

from app.cache.embedding_cache import EmbeddingCache
from app.core.config import Settings, get_settings


def _mock_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic L2-normalized vector from text (Harness/CI without API key)."""
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for i in range(0, len(block) - 3, 4):
            if len(values) >= dimensions:
                break
            n = int.from_bytes(block[i : i + 4], "big")
            values.append((n / 2**32) * 2 - 1)
        counter += 1

    norm = math.sqrt(sum(x * x for x in values))
    if norm == 0:
        return values
    return [x / norm for x in values]


class EmbeddingService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        redis: Redis | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._redis = redis
        self._cache: EmbeddingCache | None = None
        self._live: OpenAIEmbeddings | None = None
        if not self._settings.use_mock_embedding:
            kwargs: dict[str, object] = {
                "model": self._settings.embedding_model,
                "dimensions": self._settings.embedding_dimensions,
                # DashScope expects raw strings, not tiktoken token ids.
                "check_embedding_ctx_length": False,
            }
            if self._settings.openai_api_key:
                kwargs["api_key"] = self._settings.openai_api_key
            base_url = (
                self._settings.embedding_api_base or self._settings.openai_api_base
            )
            if base_url:
                kwargs["base_url"] = base_url
            self._live = OpenAIEmbeddings(**kwargs)

    @property
    def use_mock(self) -> bool:
        return self._settings.use_mock_embedding

    @property
    def model_label(self) -> str:
        """Stored on documents.metadata to invalidate skip when model/mode changes."""
        if self.use_mock:
            return "mock"
        return self._settings.embedding_model

    @property
    def embedding_dimensions(self) -> int:
        return self._settings.embedding_dimensions

    async def _cache_client(self) -> EmbeddingCache | None:
        if not self._settings.embedding_cache_enabled:
            return None
        if self._cache is not None:
            return self._cache
        redis = self._redis
        if redis is None:
            from app.core.redis import ensure_redis

            redis = await ensure_redis()
        self._cache = EmbeddingCache(redis, self._settings)
        return self._cache if self._cache.enabled else None

    async def _read_cached_vector(self, text: str) -> list[float] | None:
        cache = await self._cache_client()
        if cache is None:
            return None
        return await cache.get_vector(
            model_label=self.model_label,
            dimensions=self.embedding_dimensions,
            text=text,
        )

    async def _write_cached_vector(self, text: str, vector: list[float]) -> None:
        cache = await self._cache_client()
        if cache is None:
            return
        await cache.set_vector(
            model_label=self.model_label,
            dimensions=self.embedding_dimensions,
            text=text,
            vector=vector,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        dim = self.embedding_dimensions
        results: list[list[float] | None] = [None] * len(texts)
        misses: list[tuple[int, str]] = []

        for index, text in enumerate(texts):
            cached = await self._read_cached_vector(text)
            if cached is not None:
                results[index] = cached
            else:
                misses.append((index, text))

        if not misses:
            return [vector for vector in results if vector is not None]

        if self.use_mock:
            for index, text in misses:
                vector = _mock_embedding(text, dim)
                results[index] = vector
                await self._write_cached_vector(text, vector)
            return [vector for vector in results if vector is not None]

        assert self._live is not None
        miss_texts = [text for _, text in misses]
        vectors = await self._live.aembed_documents(miss_texts)
        self._validate_batch(vectors)
        for (index, text), vector in zip(misses, vectors, strict=True):
            results[index] = vector
            await self._write_cached_vector(text, vector)
        return [vector for vector in results if vector is not None]

    async def embed_query(self, query: str) -> list[float]:
        cached = await self._read_cached_vector(query)
        if cached is not None:
            return cached

        if self.use_mock:
            vector = _mock_embedding(query, self.embedding_dimensions)
        else:
            assert self._live is not None
            vector = await self._live.aembed_query(query)
            self._validate_one(vector)

        await self._write_cached_vector(query, vector)
        return vector

    def _validate_one(self, vector: list[float]) -> None:
        expected = self._settings.embedding_dimensions
        if len(vector) != expected:
            raise ValueError(
                f"embedding dimension mismatch: got {len(vector)}, expected {expected}"
            )

    def _validate_batch(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            self._validate_one(vector)
