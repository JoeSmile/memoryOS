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
# Mock embed is hash-based: only exact text match guarantees top hit.
SEEDED_QUERY = (
    "[Match] 2022 FIFA Men's World Cup · Argentina vs France · final · 2022-12-18\n"
    "Score: 3-3 (ET), penalties 4-2. Stadium: Lusail Stadium, Lusail.\n"
    "Goals: Lionel Messi (pen) (23'), Ángel Di María (36'), Kylian Mbappé (pen) (80'), "
    "Kylian Mbappé (81'), Lionel Messi (108'), Kylian Mbappé (pen) (118')."
)


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


@pytest.fixture(autouse=True)
def _clear_worldcup_ingest_locks():
    from app.cache import ingest_lock
    from app.cache.keys import worldcup_ingest_stem_lock_key
    from app.core.config import settings
    from app.services.knowledge_ingest_service import DEFAULT_COLLECTION_STEMS

    def _clear() -> None:
        ingest_lock._LOCAL_KEYS.clear()
        if not settings.redis_url:
            return
        import redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            keys = [
                worldcup_ingest_stem_lock_key(stem) for stem in DEFAULT_COLLECTION_STEMS
            ]
            client.delete(*keys)
        finally:
            client.close()

    _clear()
    yield
    _clear()


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
        assert (
            item["documents_created"]
            + item["documents_updated"]
            + item.get("documents_skipped", 0)
        ) == SAMPLES_LINE_COUNT


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
        assert item["documents_updated"] == 0
        assert item["documents_skipped"] == SAMPLES_LINE_COUNT


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
async def test_knowledge_ingest_rejects_when_stem_lock_held(mock_embedding, monkeypatch):
    from app.cache.ingest_lock import WorldcupIngestLock

    async def _no_redis():
        yield None

    monkeypatch.setattr("app.api.v1.knowledge.get_redis", _no_redis)

    lock = WorldcupIngestLock(None)
    assert await lock.try_acquire((SAMPLES_STEM,))
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _register_and_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                "/api/v1/knowledge/ingest/worldcup",
                headers=headers,
                json={"collections": [SAMPLES_STEM]},
            )
            assert resp.status_code == 409
            body = resp.json()
            assert body["code"] == 40902
            assert body["message"] == "ingest_in_progress"
    finally:
        await lock.release((SAMPLES_STEM,))


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
