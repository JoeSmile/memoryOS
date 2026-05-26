import pytest

from app.core.config import settings
from app.core.database import engine


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    """Harness / unit 自包含，不依赖本地 .env 是否配置 JWT_SECRET。"""
    monkeypatch.setattr(
        settings,
        "jwt_secret",
        "test-secret-for-pytest-at-least-32-chars",
    )
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")


@pytest.fixture(autouse=True)
async def reset_db_engine():
    """避免 pytest 各用例事件循环与 asyncpg 连接池错位。"""
    yield
    await engine.dispose()
