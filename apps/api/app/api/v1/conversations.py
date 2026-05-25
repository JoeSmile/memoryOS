from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.response import success
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    service = ConversationService(db, redis=redis)
    items = await service.list_for_user(user_id)
    await db.commit()
    return success(data=[item.model_dump() for item in items])


@router.post("")
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    service = ConversationService(db, redis=redis)
    conversation = await service.create(
        user_id=body.user_id,
        title=body.title,
    )
    await db.commit()
    await service.invalidate_list_cache(body.user_id)
    return success(data=ConversationRead.model_validate(conversation).model_dump())
