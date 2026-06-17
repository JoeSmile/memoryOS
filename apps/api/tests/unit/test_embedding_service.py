"""EmbeddingService mock path: deterministic 1024-d vectors without network."""

import math

import pytest

from app.core.config import Settings
from app.core.rag_constants import EMBEDDING_DIMENSIONS
from app.services.embedding_service import EmbeddingService, _mock_embedding


@pytest.fixture
def mock_service() -> EmbeddingService:
    return EmbeddingService(settings=Settings(openai_api_key=None))


def test_mock_embedding_is_l2_normalized():
    vector = _mock_embedding("hello", EMBEDDING_DIMENSIONS)
    norm = math.sqrt(sum(x * x for x in vector))
    assert len(vector) == EMBEDDING_DIMENSIONS
    assert abs(norm - 1.0) < 1e-6


def test_mock_embedding_same_text_same_vector():
    a = _mock_embedding("Messi World Cup", EMBEDDING_DIMENSIONS)
    b = _mock_embedding("Messi World Cup", EMBEDDING_DIMENSIONS)
    assert a == b


def test_mock_embedding_different_texts_differ():
    a = _mock_embedding("alpha", EMBEDDING_DIMENSIONS)
    b = _mock_embedding("beta", EMBEDDING_DIMENSIONS)
    assert a != b


@pytest.mark.asyncio
async def test_service_uses_mock_without_api_key(mock_service: EmbeddingService):
    assert mock_service.use_mock is True


@pytest.mark.asyncio
async def test_embed_query_deterministic(mock_service: EmbeddingService):
    first = await mock_service.embed_query("query-one")
    second = await mock_service.embed_query("query-one")
    assert first == second
    assert len(first) == EMBEDDING_DIMENSIONS


@pytest.mark.asyncio
async def test_embed_texts_matches_query_for_same_string(mock_service: EmbeddingService):
    query_vec = await mock_service.embed_query("shared")
    batch = await mock_service.embed_texts(["shared"])
    assert batch[0] == query_vec


@pytest.mark.asyncio
async def test_embed_texts_empty_returns_empty(mock_service: EmbeddingService):
    assert await mock_service.embed_texts([]) == []


@pytest.mark.asyncio
async def test_live_uses_embedding_base_url_when_set(monkeypatch):
    captured: dict[str, object] = {}

    class FakeEmbeddings:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        async def aembed_query(self, query: str) -> list[float]:
            return [0.0] * EMBEDDING_DIMENSIONS

    monkeypatch.setattr(
        "app.services.embedding_service.OpenAIEmbeddings",
        FakeEmbeddings,
    )
    settings = Settings(
        openai_api_key="ollama",
        openai_api_base="http://chat-host:11434/v1",
        embedding_api_base="http://embed-host:11434/v1",
        embedding_model="mxbai-embed-large",
        _env_file=None,
    )
    service = EmbeddingService(settings=settings)
    await service.embed_query("test")

    assert captured["base_url"] == "http://embed-host:11434/v1"
    assert captured["model"] == "mxbai-embed-large"


@pytest.mark.asyncio
async def test_live_falls_back_to_chat_base_url(monkeypatch):
    captured: dict[str, object] = {}

    class FakeEmbeddings:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        async def aembed_query(self, query: str) -> list[float]:
            return [0.0] * EMBEDDING_DIMENSIONS

    monkeypatch.setattr(
        "app.services.embedding_service.OpenAIEmbeddings",
        FakeEmbeddings,
    )
    settings = Settings(
        openai_api_key="ollama",
        openai_api_base="http://chat-host:11434/v1",
        embedding_model="mxbai-embed-large",
        _env_file=None,
    )
    service = EmbeddingService(settings=settings)
    await service.embed_query("test")

    assert captured["base_url"] == "http://chat-host:11434/v1"


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
async def test_embed_query_cache_hit_skips_provider(memory_redis):
    fake_redis, _store = memory_redis
    call_count = 0

    class FakeEmbeddings:
        async def aembed_query(self, query: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [0.1] * EMBEDDING_DIMENSIONS

    settings = Settings(
        openai_api_key="test-key",
        embedding_cache_enabled=True,
        _env_file=None,
    )
    service = EmbeddingService(
        settings=settings,
        redis=fake_redis,  # type: ignore[arg-type]
    )
    service._live = FakeEmbeddings()  # noqa: SLF001

    first = await service.embed_query("  World   Cup  2022  ")
    second = await service.embed_query("World Cup 2022")

    assert first == second
    assert call_count == 1


@pytest.mark.asyncio
async def test_embed_query_cache_disabled_always_calls_provider(memory_redis):
    fake_redis, _store = memory_redis
    call_count = 0

    class FakeEmbeddings:
        async def aembed_query(self, query: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [0.2] * EMBEDDING_DIMENSIONS

    settings = Settings(
        openai_api_key="test-key",
        embedding_cache_enabled=False,
        _env_file=None,
    )
    service = EmbeddingService(
        settings=settings,
        redis=fake_redis,  # type: ignore[arg-type]
    )
    service._live = FakeEmbeddings()  # noqa: SLF001

    await service.embed_query("same query")
    await service.embed_query("same query")

    assert call_count == 2


@pytest.mark.asyncio
async def test_embed_texts_partial_cache_hit(memory_redis):
    fake_redis, store = memory_redis
    call_count = 0

    class FakeEmbeddings:
        async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
            nonlocal call_count
            call_count += 1
            return [[0.3] * EMBEDDING_DIMENSIONS for _ in texts]

    settings = Settings(
        openai_api_key="test-key",
        embedding_cache_enabled=True,
        _env_file=None,
    )
    service = EmbeddingService(
        settings=settings,
        redis=fake_redis,  # type: ignore[arg-type]
    )
    service._live = FakeEmbeddings()  # noqa: SLF001

    first_batch = await service.embed_texts(["alpha", "beta"])
    assert len(first_batch) == 2
    assert call_count == 1
    assert len(store) == 2

    second_batch = await service.embed_texts(["alpha", "gamma"])
    assert second_batch[0] == first_batch[0]
    assert call_count == 2
