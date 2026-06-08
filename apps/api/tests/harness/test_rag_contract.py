"""L1 Harness：RAG ingest / search 契约（mock embed，需 PostgreSQL + migrate）。"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

SAMPLES_STEM = "samples"
SAMPLES_COLLECTION = "worldcup-samples"
SAMPLES_LINE_COUNT = 10
SEEDED_QUERY = "Argentina vs France final 2022-12-18"


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


async def _register_and_login(client: AsyncClient) -> str:
    email = f"rag-{uuid.uuid4()}@example.com"
    password = "harness-password-8"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert reg.status_code == 200

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["data"]["access_token"]


async def _ingest_samples(client: AsyncClient, headers: dict[str, str]) -> dict:
    resp = await client.post(
        "/api/v1/knowledge/ingest/worldcup",
        headers=headers,
        json={"collections": [SAMPLES_STEM]},
    )
    assert resp.status_code == 200
    body = resp.json()
    _envelope(body)
    return body["data"]


@pytest.fixture
def mock_embedding(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.mark.asyncio
async def test_knowledge_search_requires_auth(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={"query": SEEDED_QUERY, "top_k": 3},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_knowledge_ingest_requires_auth(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/knowledge/ingest/worldcup",
            json={"collections": [SAMPLES_STEM]},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_knowledge_ingest_worldcup_samples(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        data = await _ingest_samples(client, headers)
        assert data["total_lines"] == SAMPLES_LINE_COUNT
        collections = {item["collection"]: item for item in data["collections"]}
        assert SAMPLES_COLLECTION in collections
        item = collections[SAMPLES_COLLECTION]
        assert item["lines_read"] == SAMPLES_LINE_COUNT
        assert item["documents_created"] + item["documents_updated"] == SAMPLES_LINE_COUNT


@pytest.mark.asyncio
async def test_knowledge_ingest_idempotent_samples(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        await _ingest_samples(client, headers)
        second = await _ingest_samples(client, headers)

        collections = {item["collection"]: item for item in second["collections"]}
        item = collections[SAMPLES_COLLECTION]
        assert item["lines_read"] == SAMPLES_LINE_COUNT
        assert item["documents_created"] == 0
        assert item["documents_updated"] == SAMPLES_LINE_COUNT


@pytest.mark.asyncio
async def test_knowledge_search_returns_ranked_chunks(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        await _ingest_samples(client, headers)

        resp = await client.post(
            "/api/v1/knowledge/search",
            headers=headers,
            json={"query": SEEDED_QUERY, "top_k": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        _envelope(body)

        chunks = body["data"]["chunks"]
        assert len(chunks) >= 1
        first = chunks[0]
        for key in (
            "content",
            "score",
            "document_id",
            "external_id",
            "entity_type",
            "collection",
        ):
            assert key in first

        scores = [chunk["score"] for chunk in chunks]
        assert scores == sorted(scores, reverse=True)
        assert any("Argentina" in chunk["content"] for chunk in chunks)


@pytest.mark.asyncio
async def test_knowledge_search_collection_filter(mock_embedding):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        await _ingest_samples(client, headers)

        resp = await client.post(
            "/api/v1/knowledge/search",
            headers=headers,
            json={
                "query": SEEDED_QUERY,
                "collection": SAMPLES_COLLECTION,
                "top_k": 5,
            },
        )
        assert resp.status_code == 200
        chunks = resp.json()["data"]["chunks"]
        assert len(chunks) >= 1
        assert all(chunk["collection"] == SAMPLES_COLLECTION for chunk in chunks)
