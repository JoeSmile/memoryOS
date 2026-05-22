from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    items = await service.list_for_user(user_id)
    await db.commit()
    return success(
        data=[ConversationRead.model_validate(c).model_dump() for c in items],
    )


@router.post("")
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    conversation = await service.create(
        user_id=body.user_id,
        title=body.title,
    )
    await db.commit()
    return success(data=ConversationRead.model_validate(conversation).model_dump())
