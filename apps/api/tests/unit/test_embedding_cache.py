"""EmbeddingCache unit tests."""

import json

import pytest

from app.cache.embedding_cache import (
    EmbeddingCache,
    embedding_text_digest,
    normalize_embedding_text,
)
from app.core.config import Settings
from app.core.rag_constants import EMBEDDING_DIMENSIONS


def test_normalize_embedding_text_collapses_whitespace():
    assert normalize_embedding_text("  hello   world  ") == "hello world"


def test_embedding_text_digest_ignores_outer_whitespace():
    assert embedding_text_digest("  query  ") == embedding_text_digest("query")


@pytest.fixture
def memory_redis():
    store: dict[str, str] = {}

    class FakeRedis:
        async def get(self, key: str) -> str | None:
            return store.get(key)

        async def setex(self, key: str, ttl: int, value: str) -> None:
            store[key] = value

    return FakeRedis(), store


@pytest.mark.asyncio
async def test_embedding_cache_round_trip(memory_redis):
    fake_redis, store = memory_redis
    cache = EmbeddingCache(fake_redis, Settings(embedding_cache_enabled=True, embedding_cache_ttl_seconds=3600, _env_file=None))  # type: ignore[arg-type]
    vector = [0.5] * EMBEDDING_DIMENSIONS

    assert await cache.get_vector(
        model_label="text-embedding-v4",
        dimensions=EMBEDDING_DIMENSIONS,
        text="cached text",
    ) is None

    await cache.set_vector(
        model_label="text-embedding-v4",
        dimensions=EMBEDDING_DIMENSIONS,
        text="cached text",
        vector=vector,
    )
    assert len(store) == 1

    loaded = await cache.get_vector(
        model_label="text-embedding-v4",
        dimensions=EMBEDDING_DIMENSIONS,
        text="  cached   text ",
    )
    assert loaded == vector


@pytest.mark.asyncio
async def test_embedding_cache_disabled_when_flag_off(memory_redis):
    fake_redis, store = memory_redis
    cache = EmbeddingCache(
        fake_redis,  # type: ignore[arg-type]
        Settings(embedding_cache_enabled=False, _env_file=None),
    )
    vector = [0.1] * EMBEDDING_DIMENSIONS

    await cache.set_vector(
        model_label="mock",
        dimensions=EMBEDDING_DIMENSIONS,
        text="x",
        vector=vector,
    )
    assert store == {}
    assert (
        await cache.get_vector(
            model_label="mock",
            dimensions=EMBEDDING_DIMENSIONS,
            text="x",
        )
        is None
    )


@pytest.mark.asyncio
async def test_embedding_cache_rejects_wrong_dimension_payload(memory_redis):
    fake_redis, store = memory_redis
    cache = EmbeddingCache(
        fake_redis,  # type: ignore[arg-type]
        Settings(embedding_cache_enabled=True, _env_file=None),
    )
    key = cache._key(  # noqa: SLF001
        model_label="mock",
        dimensions=EMBEDDING_DIMENSIONS,
        text="bad",
    )
    store[key] = json.dumps([0.1, 0.2])

    assert (
        await cache.get_vector(
            model_label="mock",
            dimensions=EMBEDDING_DIMENSIONS,
            text="bad",
        )
        is None
    )
