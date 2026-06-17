import pytest

from app.cache import token_quota_reserve as token_quota_reserve_module
from app.core import rate_limit as rate_limit_module
from app.core.config import settings
from app.core.database import engine
from app.core.redis import discard_redis


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    """Harness / unit 自包含，不依赖本地 .env 是否配置 JWT_SECRET。"""
    monkeypatch.setattr(
        settings,
        "jwt_secret",
        "test-secret-for-pytest-at-least-32-chars",
    )
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    # Local .env may enable llm-injection-guard; its middleware scan blocks SSE harness.
    monkeypatch.setattr(settings, "llm_injection_guard_enabled", False)


@pytest.fixture(autouse=True)
async def reset_async_clients():
    """避免 pytest function 级事件循环与 asyncpg / Redis 客户端错位导致 SSE 挂起。"""
    await engine.dispose()
    discard_redis()
    rate_limit_module._script_sha = None
    token_quota_reserve_module._LOCAL_TOTAL.clear()
    token_quota_reserve_module._LOCAL_STREAM.clear()
    yield
    await engine.dispose()
    discard_redis()
    rate_limit_module._script_sha = None
    token_quota_reserve_module._LOCAL_TOTAL.clear()
    token_quota_reserve_module._LOCAL_STREAM.clear()
