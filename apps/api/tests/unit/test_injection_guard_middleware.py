"""InjectionGuardMiddleware must replay body then delegate receive for SSE disconnect."""

from __future__ import annotations

import json

import pytest
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.core.config import settings
from app.middleware.injection_guard import InjectionGuardMiddleware


@pytest.fixture
def enable_injection_guard(monkeypatch):
    monkeypatch.setattr(settings, "llm_injection_guard_enabled", True)
    yield


@pytest.mark.asyncio
async def test_replay_receive_delegates_to_original_after_body(enable_injection_guard):
    """After buffered POST body is replayed once, http.disconnect must reach the inner app."""
    receive_calls: list[str] = []
    disconnect_observed = False
    body_delivered = False

    body = json.dumps({"content": "hello harness"}).encode()

    async def scoped_receive():
        nonlocal body_delivered
        if not body_delivered:
            body_delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        receive_calls.append("original")
        return {"type": "http.disconnect"}

    async def inner_app(scope, receive, send):
        nonlocal disconnect_observed
        request = Request(scope, receive)
        body_msg = await request.receive()
        assert body_msg["type"] == "http.request"
        disconnect_msg = await request.receive()
        disconnect_observed = disconnect_msg["type"] == "http.disconnect"
        response = PlainTextResponse("ok")
        await response(scope, receive, send)

    middleware = InjectionGuardMiddleware(inner_app)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/chat/completions",
        "headers": [],
        "query_string": b"",
    }

    sent = False

    async def send(message):
        nonlocal sent
        if message["type"] == "http.response.start":
            sent = True

    # Middleware reads POST body via scoped_receive, then inner app observes disconnect.
    await middleware(scope, scoped_receive, send)

    assert sent
    assert disconnect_observed
    assert "original" in receive_calls
