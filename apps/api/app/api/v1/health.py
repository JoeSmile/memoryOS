from fastapi import APIRouter

from app.core.response import success
from app.services.health_service import build_health_data

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return success(data=await build_health_data())
