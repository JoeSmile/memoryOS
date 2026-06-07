"""L1 Harness：会话 API 契约（需本地 PostgreSQL + 已 migrate）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


@pytest.mark.asyncio
async def test_conversations_create_and_list():
    transport = ASGITransport(app=app)
    email = f"harness-{uuid.uuid4()}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_resp = await client.post(
            "/api/v1/users",
            json={"email": email},
        )
        assert user_resp.status_code == 200
        user_body = user_resp.json()
        _envelope(user_body)
        user_id = user_body["data"]["id"]

        create_resp = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Harness chat"},
        )
        assert create_resp.status_code == 200
        create_body = create_resp.json()
        _envelope(create_body)
        assert create_body["data"]["title"] == "Harness chat"
        conv_id = create_body["data"]["id"]

        list_resp = await client.get(
            "/api/v1/conversations",
            params={"user_id": user_id},
        )
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        _envelope(list_body)
        ids = [c["id"] for c in list_body["data"]]
        assert conv_id in ids


@pytest.mark.asyncio
async def test_conversations_user_not_found():
    transport = ASGITransport(app=app)
    missing_user = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/conversations",
            params={"user_id": missing_user},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == 40401
        assert body["message"] == "user_not_found"


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"harness-me-{uuid.uuid4()}@example.com"
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


@pytest.mark.asyncio
async def test_conversations_me_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/conversations/me")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 40101


@pytest.mark.asyncio
async def test_conversations_me_returns_owned_newest_first():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        first = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "First"},
        )
        assert first.status_code == 200
        first_id = first.json()["data"]["id"]

        second = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Second"},
        )
        assert second.status_code == 200
        second_id = second.json()["data"]["id"]

        list_resp = await client.get("/api/v1/conversations/me", headers=headers)
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        _envelope(list_body)
        ids = [c["id"] for c in list_body["data"]]
        assert second_id in ids
        assert first_id in ids
        assert ids[0] == second_id


@pytest.mark.asyncio
async def test_conversations_me_orders_by_last_message_activity(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        older = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Older"},
        )
        assert older.status_code == 200
        older_id = older.json()["data"]["id"]

        newer = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Newer"},
        )
        assert newer.status_code == 200
        newer_id = newer.json()["data"]["id"]

        list_before = await client.get("/api/v1/conversations/me", headers=headers)
        assert list_before.json()["data"][0]["id"] == newer_id

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": older_id, "content": "ping"},
        ) as stream_resp:
            async for _line in stream_resp.aiter_lines():
                pass

        list_after = await client.get("/api/v1/conversations/me", headers=headers)
        assert list_after.status_code == 200
        ids = [c["id"] for c in list_after.json()["data"]]
        assert ids[0] == older_id
        assert newer_id in ids


@pytest.mark.asyncio
async def test_conversations_invalid_user_id_query():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/conversations",
            params={"user_id": "not-a-uuid"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == 422
