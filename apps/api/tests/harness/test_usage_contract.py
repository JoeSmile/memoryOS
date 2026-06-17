"""L1 Harness：token usage 契约（需 PostgreSQL + mock LLM）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.graphs.chat_graph import build_chat_graph
from app.graphs.nodes import mock_model
from app.main import app
from app.models.token_usage import TokenUsage
from app.services.token_quota_service import (
    DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE,
    TOKEN_QUOTA_EXCEEDED_KEY,
)


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"usage-{uuid.uuid4()}@example.com"
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
    monkeypatch.setattr(settings, "agent_tools_enabled", False)
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


@pytest.mark.asyncio
async def test_chat_completion_records_mock_token_usage():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "usage harness"},
        )
        assert conv.status_code == 200
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as resp:
            assert resp.status_code == 200
            async for _line in resp.aiter_lines():
                pass

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count())
                .select_from(TokenUsage)
                .where(TokenUsage.user_id == uuid.UUID(user_id))
            )
            count = int(result.scalar_one())
            assert count == 1

            row = (
                await session.execute(
                    select(TokenUsage).where(
                        TokenUsage.user_id == uuid.UUID(user_id)
                    )
                )
            ).scalar_one()
            assert row.total_tokens == mock_model.MOCK_TOKEN_USAGE["total_tokens"]


@pytest.mark.asyncio
async def test_chat_completion_returns_42902_when_daily_quota_exceeded(monkeypatch):
    monkeypatch.setattr(settings, "token_quota_enabled", True)
    quota = mock_model.MOCK_TOKEN_USAGE["total_tokens"]
    monkeypatch.setattr(settings, "user_daily_token_quota", quota)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "quota harness"},
        )
        assert conv.status_code == 200
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as first:
            assert first.status_code == 200
            async for _line in first.aiter_lines():
                pass

        limited = await client.post(
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": conversation_id, "content": "再来一条"},
        )
        assert limited.status_code == 429
        body = limited.json()
        assert body["code"] == 42902
        assert body["message"] == TOKEN_QUOTA_EXCEEDED_KEY
        assert body["data"]["detail"] == DAILY_TOKEN_QUOTA_EXCEEDED_MESSAGE


@pytest.mark.asyncio
async def test_chat_completion_records_usage_with_agent_tools(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "agent_tools_enabled", True)
    monkeypatch.setattr(settings, "rag_chat_enabled", False)
    build_chat_graph.cache_clear()

    expected_total = (
        mock_model.MOCK_TOKEN_USAGE["total_tokens"]
        + mock_model.MOCK_AFTER_TOOL_TOKEN_USAGE["total_tokens"]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "agent tools usage"},
        )
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": conversation_id, "content": "联网查一下"},
        ) as resp:
            assert resp.status_code == 200
            async for _line in resp.aiter_lines():
                pass

        async with AsyncSessionLocal() as session:
            row = (
                await session.execute(
                    select(TokenUsage).where(
                        TokenUsage.user_id == uuid.UUID(user_id)
                    )
                )
            ).scalar_one()
            assert row.total_tokens == expected_total

    build_chat_graph.cache_clear()


@pytest.mark.asyncio
async def test_usage_me_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/usage/me")
        assert resp.status_code == 401
        assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_usage_me_returns_today_totals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        empty = await client.get("/api/v1/usage/me", headers=headers)
        assert empty.status_code == 200
        assert empty.json()["data"]["total_tokens"] == 0

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "usage me harness"},
        )
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers=headers,
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as resp:
            assert resp.status_code == 200
            async for _line in resp.aiter_lines():
                pass

        usage = await client.get("/api/v1/usage/me", headers=headers)
        assert usage.status_code == 200
        data = usage.json()["data"]
        assert data["total_tokens"] == mock_model.MOCK_TOKEN_USAGE["total_tokens"]
        assert data["quota_enabled"] is False
        assert data["daily_quota"] is None
