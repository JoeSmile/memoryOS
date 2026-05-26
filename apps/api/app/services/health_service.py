from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.redis import ensure_redis, ping_redis
from app.schemas.common import HealthData


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
    client = await ensure_redis()
    if client is None:
        return "disabled"
    return "ok" if await ping_redis(client) else "down"


async def build_health_data() -> dict:
    """根路径与 /api/v1/health 共用。"""
    return HealthData(
        status="ok",
        app=settings.app_name,
        env=settings.env,
        postgres=await probe_postgres(),
        redis=await probe_redis(),
    ).model_dump()
