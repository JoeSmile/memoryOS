"""L1 Harness：聊天 SSE 与消息契约（TDD — 路由未接时红灯）。"""

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
    email = f"chat-{uuid.uuid4()}@example.com"
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
async def test_chat_completions_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat/completions",
            json={
                "conversation_id": str(uuid.uuid4()),
                "content": "hello",
            },
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 40101


@pytest.mark.asyncio
async def test_chat_completions_sse_mock_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Harness chat"},
        )
        assert conv.status_code == 200
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

            events: list[dict] = []
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                payload = json.loads(line.removeprefix("data:").strip())
                events.append(payload)

        token_events = [e for e in events if e.get("event") == "token"]
        done_events = [e for e in events if e.get("event") == "done"]
        assert token_events
        assert "".join(e["data"]["content"] for e in token_events) == "你好！"
        assert done_events
        assert done_events[0]["data"]["message_id"]
        assert done_events[0]["data"]["stream_id"]


@pytest.mark.asyncio
async def test_list_messages_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/conversations/{uuid.uuid4()}/messages")
        assert resp.status_code == 401
        assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_list_messages_after_sse_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Harness messages"},
        )
        conversation_id = conv.json()["data"]["id"]

        async with client.stream(
            "POST",
            "/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={"conversation_id": conversation_id, "content": "你好"},
        ) as stream_resp:
            async for _line in stream_resp.aiter_lines():
                pass

        list_resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        _envelope(list_resp.json())
        roles = [m["role"] for m in list_resp.json()["data"]]
        assert roles == ["user", "assistant"]


@pytest.mark.asyncio
async def test_chat_completions_foreign_conversation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, user_a = await _register_and_login(client)
        token_b, _user_b = await _register_and_login(client)

        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_a, "title": "Owner only"},
        )
        conversation_id = conv.json()["data"]["id"]

        resp = await client.post(
            "/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"conversation_id": conversation_id, "content": "hi"},
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == 40401
        assert resp.json()["message"] == "conversation_not_found"
