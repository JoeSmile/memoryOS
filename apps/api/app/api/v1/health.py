from fastapi import APIRouter

from app.core.config import settings
from app.core.response import success
from app.schemas.common import HealthData
from app.services.health_service import probe_postgres, probe_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    postgres = await probe_postgres()
    redis = await probe_redis()
    return success(
        data=HealthData(
            status="ok",
            app=settings.app_name,
            env=settings.env,
            postgres=postgres,
            redis=redis,
        ).model_dump(),
    )
