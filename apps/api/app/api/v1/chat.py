import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models import User
from app.core.response import success
from app.schemas.message import ChatCancelRequest, ChatCompletionRequest
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
    await service.prepare_completion_turn(
        conversation_id=body.conversation_id,
        user_id=user.id,
        content=body.content,
        client_message_id=body.client_message_id,
        regenerate=body.regenerate,
    )

    stream_state = service.new_completion_stream_state(
        conversation_id=body.conversation_id,
        user_id=user.id,
    )

    async def event_generator():
        try:
            async for event in service.stream_completion_events(
                stream_state=stream_state,
                request=request,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            assistant_id = await service.finalize_completion_stream(stream_state)
            if assistant_id is not None:
                done_frame = {
                    "event": "done",
                    "data": {
                        "message_id": str(assistant_id),
                        "stream_id": stream_state.stream_id,
                    },
                }
                yield f"data: {json.dumps(done_frame, ensure_ascii=False)}\n\n"
        finally:
            if not stream_state.persisted:
                await service.finalize_completion_stream(stream_state)
            await service.release_turn_inflight_lock(
                body.conversation_id,
                body.client_message_id,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Stream-Id": stream_state.stream_id},
    )


@router.post("/completions/cancel")
async def chat_completions_cancel(
    body: ChatCancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    service = ChatService(db, redis=redis)
    await service.cancel_stream(
        stream_id=str(body.stream_id),
        user_id=user.id,
        visible_content=body.visible_content,
        visible_length=body.visible_length,
    )
    return success()
