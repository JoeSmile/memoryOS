"""L1 Harness：慢 SSE 流期间其它 Chat/DB 请求不得假死（Depends 生命周期回归）。"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.database import engine
from app.graphs.chat_graph import build_chat_graph
from app.main import app


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"lifecycle-{uuid.uuid4()}@example.com"
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


async def _create_conversation(
    client: AsyncClient,
    *,
    token: str,
    user_id: str,
    title: str,
) -> str:
    conv = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": user_id, "title": title},
    )
    assert conv.status_code == 200
    return conv.json()["data"]["id"]


async def _collect_sse_events(resp) -> list[dict]:
    events: list[dict] = []
    async for line in resp.aiter_lines():
        if not line.startswith("data:"):
            continue
        events.append(json.loads(line.removeprefix("data:").strip()))
    return events


@pytest.fixture(autouse=True)
def slow_mock_llm(monkeypatch):
    """Mock LLM 慢流：prepare 很快结束，token 间隔拉长以便并发探测。"""
    from app.graphs.nodes import mock_model

    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "agent_tools_enabled", False)

    async def slow_tokens():
        async for token in mock_model.mock_stream_tokens_slow(delay_seconds=0.25):
            yield token

    monkeypatch.setattr(mock_model, "mock_stream_tokens", slow_tokens)
    build_chat_graph.cache_clear()
    yield
    build_chat_graph.cache_clear()


@pytest.mark.asyncio
async def test_list_conversations_during_slow_sse_stream():
    """慢 SSE 进行中，会话列表（短 DB 借用）须在数秒内返回，不得等流结束。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, user_id = await _register_and_login(client)
        conversation_id = await _create_conversation(
            client,
            token=token,
            user_id=user_id,
            title="Lifecycle slow stream",
        )

        slow_stream_task: asyncio.Task[list[dict]] | None = None

        async def consume_slow_stream() -> list[dict]:
            async with client.stream(
                "POST",
                "/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json={"conversation_id": conversation_id, "content": "慢流探测"},
            ) as resp:
                assert resp.status_code == 200
                return await _collect_sse_events(resp)

        slow_stream_task = asyncio.create_task(consume_slow_stream())

        # 等 start 帧，确认 SSE 已进入流式阶段（prepare 已结束）。
        for _ in range(40):
            if slow_stream_task.done():
                break
            await asyncio.sleep(0.05)

        async def list_while_streaming() -> None:
            listed = await client.get(
                "/api/v1/conversations",
                params={"user_id": user_id},
            )
            assert listed.status_code == 200
            assert listed.json()["code"] == 0

        await asyncio.wait_for(list_while_streaming(), timeout=3.0)

        events = await asyncio.wait_for(slow_stream_task, timeout=15.0)
        assert any(event.get("event") == "done" for event in events)


@pytest.mark.asyncio
async def test_second_chat_prepare_while_slow_sse_stream(monkeypatch):
    """第一条 SSE 仍在吐 token 时，第二条 chat 的 prepare 须快速 200（非 pool 假死）。"""
    import app.core.database as db_module
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    await engine.dispose()
    tight_engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=0,
        pool_timeout=2,
    )
    tight_session = async_sessionmaker(
        tight_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    monkeypatch.setattr(db_module, "engine", tight_engine)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", tight_session)

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token, user_id = await _register_and_login(client)
            conv_a = await _create_conversation(
                client,
                token=token,
                user_id=user_id,
                title="Stream A",
            )
            conv_b = await _create_conversation(
                client,
                token=token,
                user_id=user_id,
                title="Stream B",
            )

            async def consume_stream_a() -> list[dict]:
                async with client.stream(
                    "POST",
                    "/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"conversation_id": conv_a, "content": "第一条慢流"},
                ) as resp:
                    assert resp.status_code == 200
                    return await _collect_sse_events(resp)

            stream_a_task = asyncio.create_task(consume_stream_a())

            # 等第一条进入 token 阶段
            await asyncio.sleep(0.35)

            async def start_stream_b() -> int:
                async with client.stream(
                    "POST",
                    "/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"conversation_id": conv_b, "content": "第二条并发"},
                ) as resp:
                    assert resp.status_code == 200
                    first_line = ""
                    async for line in resp.aiter_lines():
                        if line.startswith("data:"):
                            first_line = line
                            break
                    assert first_line.startswith("data:")
                    payload = json.loads(first_line.removeprefix("data:").strip())
                    assert payload["event"] == "start"
                    return resp.status_code

            status = await asyncio.wait_for(start_stream_b(), timeout=3.0)
            assert status == 200

            events_a = await asyncio.wait_for(stream_a_task, timeout=15.0)
            assert any(event.get("event") == "done" for event in events_a)
    finally:
        await tight_engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tcp_slow_sse_allows_concurrent_list():
    """真实 TCP（需本地 API）：`HARNESS_TCP_URL=http://127.0.0.1:8000` 时跑 nightly。"""
    base_url = os.getenv("HARNESS_TCP_URL", "").rstrip("/")
    if not base_url:
        pytest.skip("Set HARNESS_TCP_URL to run TCP lifecycle harness (e.g. nightly)")

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        token, user_id = await _register_and_login(client)
        conversation_id = await _create_conversation(
            client,
            token=token,
            user_id=user_id,
            title="TCP lifecycle",
        )

        async def consume_slow_stream() -> None:
            async with client.stream(
                "POST",
                "/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json={"conversation_id": conversation_id, "content": "TCP 慢流"},
            ) as resp:
                assert resp.status_code == 200
                async for _line in resp.aiter_lines():
                    pass

        slow_task = asyncio.create_task(consume_slow_stream())
        await asyncio.sleep(0.5)

        listed = await asyncio.wait_for(
            client.get(
                "/api/v1/conversations",
                params={"user_id": user_id},
            ),
            timeout=3.0,
        )
        assert listed.status_code == 200

        await asyncio.wait_for(slow_task, timeout=60.0)
