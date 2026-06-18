"""Per-node DB sessions for LangGraph — never borrow a session for the whole SSE lifetime."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


@asynccontextmanager
async def graph_db_session(config: RunnableConfig) -> AsyncIterator[AsyncSession]:
    """Use injected session in tests; otherwise open/close a pool connection per node."""
    configurable = config.get("configurable") or {}
    injected = configurable.get("db")
    if isinstance(injected, AsyncSession):
        yield injected
        return
    async with AsyncSessionLocal() as session:
        yield session
