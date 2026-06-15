from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.core.response import success
from app.demo.wc2022_analysis_presets import DEMO_ANALYSIS_TEMPLATES
from app.models import User
from app.repositories.wc_match_repository import WcMatchRepository
from app.schemas.demo_analysis import DemoAnalysisTemplateRead
from app.services.worldcup_match_service import (
    WC_2022_TOURNAMENT_ID,
    WorldcupMatchService,
)

router = APIRouter(prefix="/worldcup", tags=["worldcup"])


@router.get("/matches")
async def list_worldcup_matches(
    tournament_id: str = Query(
        default=WC_2022_TOURNAMENT_ID,
        description="V1 demo: only WC-2022 is supported",
    ),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if tournament_id != WC_2022_TOURNAMENT_ID:
        raise AppException(
            code=42201,
            message="tournament_not_supported",
            status_code=422,
        )

    service = WorldcupMatchService(WcMatchRepository(db))
    data = await service.list_tournament_matches(tournament_id)
    await db.commit()
    return success(data=data.model_dump())


@router.get("/demo-templates")
async def list_demo_analysis_templates(
    _user: User = Depends(get_current_user),
):
    items = [
        DemoAnalysisTemplateRead(
            id=item.id,
            label=item.label,
            description=item.description,
        ).model_dump()
        for item in DEMO_ANALYSIS_TEMPLATES
    ]
    return success(data=items)
