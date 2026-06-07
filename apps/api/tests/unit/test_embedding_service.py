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
