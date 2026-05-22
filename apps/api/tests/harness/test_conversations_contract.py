"""L1 Harness：会话 API 契约（需本地 PostgreSQL + 已 migrate）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

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
