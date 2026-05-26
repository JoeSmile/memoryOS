"""L1 Harness：JWT 注册 / 登录 / me 契约。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


@pytest.mark.asyncio
async def test_auth_register_login_and_me():
    transport = ASGITransport(app=app)
    email = f"auth-{uuid.uuid4()}@example.com"
    password = "harness-password-8"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert reg.status_code == 200
        reg_body = reg.json()
        _envelope(reg_body)
        assert reg_body["data"]["email"] == email
        user_id = reg_body["data"]["id"]

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200
        login_body = login.json()
        _envelope(login_body)
        token = login_body["data"]["access_token"]
        assert login_body["data"]["token_type"] == "bearer"
        assert token

        me = await client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        me_body = me.json()
        _envelope(me_body)
        assert me_body["data"]["id"] == user_id
        assert me_body["data"]["email"] == email


@pytest.mark.asyncio
async def test_auth_register_duplicate_email():
    transport = ASGITransport(app=app)
    email = f"auth-dup-{uuid.uuid4()}@example.com"
    password = "harness-password-8"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert first.status_code == 200

        dup = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert dup.status_code == 409
        body = dup.json()
        assert body["code"] == 40901
        assert body["message"] == "email_already_exists"


@pytest.mark.asyncio
async def test_auth_login_invalid_credentials():
    transport = ASGITransport(app=app)
    email = f"auth-{uuid.uuid4()}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "correct-password"},
        )
        bad = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert bad.status_code == 401
        body = bad.json()
        assert body["code"] == 40102
        assert body["message"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_requires_bearer_token():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/me")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 40101
