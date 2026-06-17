from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import User
from app.services.token_quota_service import TokenQuotaService

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/me")
async def read_my_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    totals = await TokenQuotaService(db).today_totals(user.id)
    await db.commit()
    return success(
        data={
            "prompt_tokens": totals.prompt_tokens,
            "completion_tokens": totals.completion_tokens,
            "total_tokens": totals.total_tokens,
            "quota_enabled": settings.token_quota_enabled,
            "daily_quota": (
                settings.user_daily_token_quota
                if settings.token_quota_enabled
                else None
            ),
        }
    )
