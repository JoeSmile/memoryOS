from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.core.response import success
from app.models import User
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.schemas.demo_analysis import DemoTurnRequest, DemoTurnResponse
from app.schemas.message import MessageRead
from app.repositories.message_repository import MessageRepository
from app.repositories.wc_match_repository import WcMatchRepository
from app.services.demo_analysis_service import DemoAnalysisService
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
    if body.initial_message is not None:
        conversation, message = await service.create_with_first_message(
            user_id=body.user_id,
            title=body.title,
            content=body.initial_message,
        )
        data = ConversationRead.model_validate(conversation).model_dump()
        data["initial_message"] = MessageRead.model_validate(message).model_dump()
    else:
        conversation = await service.create(
            user_id=body.user_id,
            title=body.title,
        )
        data = ConversationRead.model_validate(conversation).model_dump()
    await db.commit()
    await service.invalidate_list_cache(body.user_id)
    return success(data=data)


@router.get("/me")
async def list_my_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    """当前用户的会话列表（updated_at 降序），供 /chat 恢复最近一场分析。"""
    service = ConversationService(db, redis=redis)
    items = await service.list_for_user(user.id)
    await db.commit()
    return success(data=[item.model_dump() for item in items])


@router.post("/{conversation_id}/demo-turn")
async def append_demo_analysis_turn(
    conversation_id: UUID,
    body: DemoTurnRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    conversations = ConversationService(db, redis=redis)
    demo = DemoAnalysisService(
        conversations,
        MessageRepository(db),
        WcMatchRepository(db),
    )
    user_message, assistant_message = await demo.append_demo_turn(
        conversation_id=conversation_id,
        user_id=user.id,
        match_id=body.match_id,
        template_id=body.template_id,
    )
    await db.commit()
    return success(
        data=DemoTurnResponse(
            user_message_id=str(user_message.id),
            assistant_message_id=str(assistant_message.id),
        ).model_dump(),
    )


@router.get("/{conversation_id}/messages")
async def list_conversation_messages(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    items = await service.list_messages_for_user(conversation_id, user.id)
    await db.commit()
    return success(data=[item.model_dump() for item in items])
