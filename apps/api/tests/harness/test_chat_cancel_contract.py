"""L1 Harness：聊天流 cancel API 契约。"""

import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"cancel-{uuid.uuid4()}@example.com"
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


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


@pytest.mark.asyncio
async def test_chat_cancel_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat/completions/cancel",
            json={"stream_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_chat_cancel_unknown_stream_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _user_id = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/chat/completions/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={"stream_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == 40401
        assert resp.json()["message"] == "stream_not_found"


@pytest.mark.asyncio
async def test_chat_cancel_foreign_stream_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, user_a = await _register_and_login(client)
        token_b, _user_b = await _register_and_login(client)

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_a, "title": "Cancel owner"},
        )
        conversation_id = conv.json()["data"]["id"]

        stream_id: str | None = None
        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as stream_resp:
            async for line in stream_resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                event = json.loads(line.removeprefix("data:").strip())
                if event.get("event") == "start":
                    stream_id = event["data"]["stream_id"]
                    break

        assert stream_id is not None
        foreign = await client.post(
            "/api/v1/chat/completions/cancel",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"stream_id": stream_id},
        )
        assert foreign.status_code == 404
        assert foreign.json()["message"] == "stream_not_found"


@pytest.mark.asyncio
async def test_chat_cancel_foreign_stream_still_rejected_after_owner_cancelled():
    from app.cache.stream_cancel_cache import StreamCancelCache
    from app.core.redis import ensure_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, user_a = await _register_and_login(client)
        token_b, _user_b = await _register_and_login(client)

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_a, "title": "Cancel after owner cancelled"},
        )
        conversation_id = conv.json()["data"]["id"]
        stream_id = str(uuid.uuid4())
        cache = StreamCancelCache(await ensure_redis())
        await cache.register_active(
            stream_id,
            uuid.UUID(conversation_id),
            uuid.UUID(user_a),
        )
        await cache.set_cancelled(stream_id)

        foreign = await client.post(
            "/api/v1/chat/completions/cancel",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"stream_id": stream_id},
        )
        assert foreign.status_code == 404
        assert foreign.json()["message"] == "stream_not_found"

        await cache.clear(stream_id)


@pytest.mark.asyncio
async def test_chat_cancel_owned_stream_is_idempotent():
    from app.cache.stream_cancel_cache import StreamCancelCache
    from app.core.redis import ensure_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Cancel idempotent"},
        )
        conversation_id = conv.json()["data"]["id"]
        stream_id = str(uuid.uuid4())
        cache = StreamCancelCache(await ensure_redis())
        await cache.register_active(
            stream_id,
            uuid.UUID(conversation_id),
            uuid.UUID(user_id),
        )

        for _ in range(2):
            resp = await client.post(
                "/api/v1/chat/completions/cancel",
                headers={"Authorization": f"Bearer {token}"},
                json={"stream_id": stream_id},
            )
            assert resp.status_code == 200
            _envelope(resp.json())

        await cache.clear(stream_id)
