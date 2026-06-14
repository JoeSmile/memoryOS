"""L1 Harness：长期记忆 API 契约（需本地 PostgreSQL + 已 migrate）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal
from app.main import app
from app.repositories.memory_repository import MemoryRepository


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"memories-{uuid.uuid4()}@example.com"
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


async def _seed_memory(
    user_id: str,
    *,
    memory_key: str = "preference:harness",
    memory_type: str = "preference",
    content: str = "偏好简洁回答",
) -> uuid.UUID:
    async with AsyncSessionLocal() as session:
        repo = MemoryRepository(session)
        memory = await repo.upsert(
            user_id=uuid.UUID(user_id),
            memory_key=memory_key,
            memory_type=memory_type,
            content=content,
        )
        await session.commit()
        return memory.id


@pytest.mark.asyncio
async def test_memories_list_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/memories")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 40101


@pytest.mark.asyncio
async def test_memories_list_returns_owned_rows_without_embedding():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        memory_id = await _seed_memory(
            user_id,
            memory_key="fact:team",
            memory_type="fact",
            content="支持阿根廷队",
        )

        list_resp = await client.get("/api/v1/memories", headers=headers)
        assert list_resp.status_code == 200
        body = list_resp.json()
        _envelope(body)
        items = body["data"]
        assert len(items) >= 1
        row = next(item for item in items if item["id"] == str(memory_id))
        assert row["user_id"] == user_id
        assert row["memory_key"] == "fact:team"
        assert row["memory_type"] == "fact"
        assert row["content"] == "支持阿根廷队"
        assert "embedding" not in row


@pytest.mark.asyncio
async def test_memories_delete_owned_memory():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        memory_id = await _seed_memory(user_id, content="待删除记忆")

        delete_resp = await client.delete(
            f"/api/v1/memories/{memory_id}",
            headers=headers,
        )
        assert delete_resp.status_code == 200
        _envelope(delete_resp.json())

        list_resp = await client.get("/api/v1/memories", headers=headers)
        ids = [item["id"] for item in list_resp.json()["data"]]
        assert str(memory_id) not in ids


@pytest.mark.asyncio
async def test_memories_delete_cross_user_returns_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, user_a = await _register_and_login(client)
        token_b, _user_b = await _register_and_login(client)
        memory_id = await _seed_memory(user_a, content="只属于 A")

        resp = await client.delete(
            f"/api/v1/memories/{memory_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == 40401
        assert body["message"] == "memory_not_found"

        list_resp = await client.get(
            "/api/v1/memories",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        ids = [item["id"] for item in list_resp.json()["data"]]
        assert str(memory_id) in ids
