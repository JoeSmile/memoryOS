"""L1 Harness：超长历史 + 记忆裁剪后 completion 仍成功（EP06 Story 6.1 + 6.5）。"""

import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.graphs.chat_graph import build_chat_graph
from app.main import app
from app.models.message import COMPLETION_COMPLETE
from app.repositories.message_repository import MessageRepository

_SEEDED_TURNS = 31


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"memory-ctx-{uuid.uuid4()}@example.com"
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


async def _seed_long_mock_history(conversation_id: str) -> None:
    conv_id = uuid.UUID(conversation_id)
    async with AsyncSessionLocal() as session:
        repo = MessageRepository(session)
        for index in range(_SEEDED_TURNS):
            await repo.create(
                conv_id,
                "user",
                f"轮次-{index} 追问世界杯战术与阵容",
            )
            await repo.create(
                conv_id,
                "assistant",
                f"回复-{index} 简要分析",
                completion_status=COMPLETION_COMPLETE,
            )
        await session.commit()


async def _stream_chat(
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


def _assert_sse_order(events: list[dict]) -> None:
    names = [event.get("event") for event in events]
    assert names[0] == "start"
    assert "error" not in names

    start_idx = names.index("start")
    done_idx = names.index("done")
    token_indices = [i for i, name in enumerate(names) if name == "token"]
    assert token_indices
    assert all(start_idx < idx < done_idx for idx in token_indices)

    for name in names:
        assert name in {"start", "token", "sources", "done"}


@pytest.fixture(autouse=True)
def memory_context_harness(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "tavily_api_key", None)
    monkeypatch.setattr(settings, "memory_enabled", True)
    monkeypatch.setattr(settings, "agent_tools_enabled", False)
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


@pytest.mark.asyncio
async def test_long_history_completion_returns_200_and_sse_order():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conv = await client.post(
            "/api/v1/conversations",
            json={"user_id": user_id, "title": "Long memory harness"},
        )
        assert conv.status_code == 200
        conversation_id = conv.json()["data"]["id"]

        await _seed_long_mock_history(conversation_id)

        events = await _stream_chat(
            client,
            token=token,
            conversation_id=conversation_id,
            content="在超长历史后继续提问",
        )

        _assert_sse_order(events)
        token_events = [e for e in events if e.get("event") == "token"]
        assert "".join(e["data"]["content"] for e in token_events) == "你好！"
        assert events[-1]["event"] == "done"
        assert events[-1]["data"]["message_id"]

        list_resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        _envelope(list_resp.json())
        roles = [m["role"] for m in list_resp.json()["data"]]
        assert roles.count("user") == _SEEDED_TURNS + 1
        assert roles.count("assistant") == _SEEDED_TURNS + 1
