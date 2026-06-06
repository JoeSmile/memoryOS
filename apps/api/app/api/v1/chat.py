import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models import User
from app.schemas.message import ChatCompletionRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    service = ChatService(db, redis=redis)
    await service.conversations.get_owned_conversation(body.conversation_id, user.id)

    async def event_generator():
        async for event in service.stream_completion_events(
            conversation_id=body.conversation_id,
            user_id=user.id,
            content=body.content,
            request=request,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        await db.commit()
        await service.conversations.invalidate_list_cache(user.id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
