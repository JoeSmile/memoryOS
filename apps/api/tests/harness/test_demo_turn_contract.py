"""L1 Harness：demo-turn 契约（需 PostgreSQL + migrate + WC ETL）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"harness-demo-{uuid.uuid4()}@example.com"
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
async def test_demo_turn_requires_auth():
    transport = ASGITransport(app=app)
    conv_id = str(uuid.uuid4())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/demo-turn",
            json={"match_id": "M-2022-64", "template_id": "flank_attack"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 40101


@pytest.mark.asyncio
async def test_demo_turn_rejects_unknown_template():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "demo harness"},
        )
        assert conv.status_code == 200
        conv_id = conv.json()["data"]["id"]

        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/demo-turn",
            headers=headers,
            json={"match_id": "M-2022-64", "template_id": "not-a-template"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == 42201
        assert body["message"] == "demo_template_not_found"


@pytest.mark.asyncio
async def test_demo_turn_forbidden_for_other_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, user_a = await _register_and_login(client)
        token_b, _user_b = await _register_and_login(client)

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_a, "title": "owner only"},
        )
        assert conv.status_code == 200
        conv_id = conv.json()["data"]["id"]

        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/demo-turn",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"match_id": "M-2022-64", "template_id": "flank_attack"},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == 40401
        assert body["message"] == "conversation_not_found"


@pytest.mark.asyncio
async def test_demo_turn_appends_messages_when_wc_data_exists():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "wc demo"},
        )
        assert conv.status_code == 200
        conv_id = conv.json()["data"]["id"]

        empty = await client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=headers,
        )
        assert empty.status_code == 200
        assert empty.json()["data"] == []

        turn = await client.post(
            f"/api/v1/conversations/{conv_id}/demo-turn",
            headers=headers,
            json={"match_id": "M-2022-64", "template_id": "flank_attack"},
        )
        if turn.status_code == 404 and turn.json().get("message") == "match_not_found":
            pytest.skip("WC ETL data not loaded (M-2022-64 missing)")

        assert turn.status_code == 200
        turn_body = turn.json()
        _envelope(turn_body)
        assert turn_body["data"]["user_message_id"]
        assert turn_body["data"]["assistant_message_id"]

        messages = await client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=headers,
        )
        assert messages.status_code == 200
        rows = messages.json()["data"]
        assert len(rows) == 2
        assert rows[0]["role"] == "user"
        assert rows[1]["role"] == "assistant"
        assert rows[1]["metadata"]["demo"]["match_id"] == "M-2022-64"
        assert rows[1]["metadata"]["demo"]["template_id"] == "flank_attack"
        assert rows[1]["metadata"]["rag_sources"][0]["external_id"] == "M-2022-64"
