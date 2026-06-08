"""L1 Harness：RAG chat SSE 契约（mock embed + mock LLM，TDD — retrieve/SSE 未接时红灯）。"""

from __future__ import annotations

import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from tests.harness.test_rag_contract import (
    SEEDED_QUERY,
    _ingest_samples,
)

NO_HIT_QUERY = "quantum chromodynamics lattice gauge harness-no-hit-xyz"


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"rag-chat-{uuid.uuid4()}@example.com"
    password = "harness-password-8"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert reg.status_code == 200
    user_id = reg.json()["data"]["id"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return token, user_id


async def _create_conversation(
    client: AsyncClient,
    token: str,
    user_id: str,
    *,
    title: str = "Harness RAG chat",
) -> str:
    resp = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": user_id, "title": title},
    )
    assert resp.status_code == 200
    return resp.json()["data"]["id"]


async def _stream_chat_events(
    client: AsyncClient,
    *,
    token: str,
    conversation_id: str,
    content: str,
) -> list[dict]:
    events: list[dict] = []
    async with client.stream(
        "POST",
        "/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"conversation_id": conversation_id, "content": content},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            events.append(json.loads(line.removeprefix("data:").strip()))
    return events


def _event_index(events: list[dict], event_name: str) -> int:
    for index, event in enumerate(events):
        if event.get("event") == event_name:
            return index
    return -1


@pytest.fixture(autouse=True)
def _mock_rag_chat_harness(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "rag_chat_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_top_k", 5)
    monkeypatch.setattr(settings, "rag_chat_min_score", 0.35)
    monkeypatch.setattr(settings, "rag_chat_collection", None)


@pytest.fixture(autouse=True)
def _clear_worldcup_ingest_locks():
    from app.cache import ingest_lock
    from app.cache.keys import worldcup_ingest_stem_lock_key
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


@pytest.mark.asyncio
async def test_rag_chat_emits_sources_before_tokens_after_ingest():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        await _ingest_samples(client, headers)

        conversation_id = await _create_conversation(client, token, user_id)
        events = await _stream_chat_events(
            client,
            token=token,
            conversation_id=conversation_id,
            content=SEEDED_QUERY,
        )

        assert events[0]["event"] == "start"
        sources_index = _event_index(events, "sources")
        token_index = _event_index(events, "token")
        done_index = _event_index(events, "done")

        assert sources_index >= 0, "expected sources SSE after RAG retrieve"
        assert token_index >= 0
        assert done_index >= 0
        assert sources_index < token_index

        sources_event = events[sources_index]
        items = sources_event["data"]["items"]
        assert len(items) >= 1
        first = items[0]
        for key in ("external_id", "collection", "score", "content_preview"):
            assert key in first
        assert first["external_id"] == "match:M-2022-64"

        token_events = [event for event in events if event.get("event") == "token"]
        assert "".join(event["data"]["content"] for event in token_events) == "你好！"

        done_event = events[done_index]
        assert done_event["data"]["message_id"]
        assert done_event["data"].get("sources") == items


@pytest.mark.asyncio
async def test_rag_chat_no_sources_without_ingested_knowledge():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conversation_id = await _create_conversation(client, token, user_id)
        events = await _stream_chat_events(
            client,
            token=token,
            conversation_id=conversation_id,
            content=NO_HIT_QUERY,
        )

        assert _event_index(events, "sources") == -1
        assert _event_index(events, "token") >= 0
        assert _event_index(events, "done") >= 0


@pytest.mark.asyncio
async def test_rag_chat_no_sources_when_scores_below_min_threshold(monkeypatch):
    monkeypatch.setattr(settings, "rag_chat_min_score", 0.99)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        await _ingest_samples(client, headers)

        conversation_id = await _create_conversation(client, token, user_id)
        events = await _stream_chat_events(
            client,
            token=token,
            conversation_id=conversation_id,
            content=NO_HIT_QUERY,
        )

        assert _event_index(events, "sources") == -1
        assert _event_index(events, "token") >= 0
