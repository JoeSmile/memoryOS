from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import User
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("")
async def list_memories(
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    items = await service.list_for_user(user.id, limit=limit, offset=offset)
    await db.commit()
    return success(data=[item.model_dump() for item in items])


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    await service.delete_for_user(memory_id, user.id)
    await db.commit()
    return success()
