from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.redis import create_redis_client, ping_redis


async def probe_postgres() -> str:
    if not settings.database_url:
        return "disabled"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "down"


async def probe_redis() -> str:
    if not settings.redis_url:
        return "disabled"
    client = create_redis_client()
    if client is None:
        return "disabled"
    try:
        ok = await ping_redis(client)
        return "ok" if ok else "down"
    finally:
        await client.aclose()
