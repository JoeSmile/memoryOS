"""FastAPI middleware — optional llm-injection-guard on chat completions (EP09 2.11)."""

from __future__ import annotations

import json
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.exceptions import AppException
from app.services.security.llm_injection_guard_adapter import (
    assert_llm_injection_guard_user_input,
)

logger = logging.getLogger(__name__)

_CHAT_COMPLETIONS_PATH = "/api/v1/chat/completions"


class InjectionGuardMiddleware:
    """HTTP-layer compare path for llm-injection-guard; authoritative chain remains prepare_completion_turn."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.llm_injection_guard_enabled:
            await self.app(scope, receive, send)
            return

        if scope.get("method") != "POST" or scope.get("path") != _CHAT_COMPLETIONS_PATH:
            await self.app(scope, receive, send)
            return

        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        body_sent = False

        async def replay_receive() -> dict:
            # Replay buffered body once, then delegate to the original receive so
            # Request.is_disconnected() can observe http.disconnect during SSE.
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        rejection = _scan_chat_completion_body(body)
        if rejection is not None:
            response = JSONResponse(
                status_code=rejection.status_code,
                content={
                    "code": rejection.code,
                    "message": rejection.message,
                    "data": None,
                },
            )
            await response(scope, replay_receive, send)
            return

        await self.app(scope, replay_receive, send)


def _scan_chat_completion_body(body: bytes) -> AppException | None:
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    content = data.get("content")
    if not isinstance(content, str) or not content.strip():
        return None

    try:
        assert_llm_injection_guard_user_input(content)
    except AppException as exc:
        return exc
    except Exception:
        logger.exception("llm_injection_guard middleware scan failed")
        return None

    return None
