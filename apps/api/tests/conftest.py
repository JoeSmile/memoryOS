import pytest

from app.core.database import engine


@pytest.fixture(autouse=True)
async def reset_db_engine():
    """避免 pytest 各用例事件循环与 asyncpg 连接池错位。"""
    yield
    await engine.dispose()
