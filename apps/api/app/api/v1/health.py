from fastapi import APIRouter

from app.core.config import settings
from app.core.response import success
from app.schemas.common import HealthData

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return success(
        data=HealthData(
            status="ok",
            app=settings.app_name,
            env=settings.env,
        ).model_dump(),
    )
