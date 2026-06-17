"""L1 Harness：audit_log 契约（需 PostgreSQL + migrate）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal
from app.main import app
from app.repositories.audit_repository import (
    ACTION_DEMO_TURN,
    AuditRepository,
    mask_email_for_audit,
)


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"audit-{uuid.uuid4()}@example.com"
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
async def test_demo_turn_writes_audit_row():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "audit demo"},
        )
        assert conv.status_code == 200
        conv_id = conv.json()["data"]["id"]

        turn = await client.post(
            f"/api/v1/conversations/{conv_id}/demo-turn",
            headers=headers,
            json={"match_id": "M-2022-64", "template_id": "flank_attack"},
        )
        if turn.status_code == 404 and turn.json().get("message") == "match_not_found":
            pytest.skip("WC ETL data not loaded (M-2022-64 missing)")

        assert turn.status_code == 200

        async with AsyncSessionLocal() as session:
            rows = await AuditRepository(session).list_for_user_action(
                uuid.UUID(user_id),
                ACTION_DEMO_TURN,
            )
            assert len(rows) == 1
            row = rows[0]
            assert row.resource_type == "conversation"
            assert row.resource_id == conv_id
            assert row.metadata_json["template_id"] == "flank_attack"
            assert row.metadata_json["match_id"] == "M-2022-64"


@pytest.mark.asyncio
async def test_login_failed_writes_audit_row():
    transport = ASGITransport(app=app)
    email = f"audit-fail-{uuid.uuid4()}@example.com"
    password = "harness-password-8"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert reg.status_code == 200

        email_masked = mask_email_for_audit(email)
        async with AsyncSessionLocal() as session:
            repo = AuditRepository(session)
            before = len(
                await repo.list_login_failed_for_email_masked(email_masked)
            )

        bad = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert bad.status_code == 401
        assert bad.json()["code"] == 40102

        async with AsyncSessionLocal() as session:
            rows = await AuditRepository(session).list_login_failed_for_email_masked(
                email_masked
            )
            assert len(rows) == before + 1
            row = rows[0]
            assert row.user_id is None
            assert row.metadata_json["email_masked"] == email_masked
