import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.deps import get_current_user, get_current_user_id
from app.core.rate_limit import enforce_chat_rate_limit
from app.core.redis import ensure_redis
from app.core.response import success
from app.models import User
from app.schemas.message import ChatCancelRequest, ChatCompletionRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    _: None = Depends(enforce_chat_rate_limit),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    # No Depends(get_db/get_redis) on SSE — yield deps would stay open for the whole stream.
    redis: Redis | None = await ensure_redis()

    async with AsyncSessionLocal() as db:
        service = ChatService(db, redis=redis)
        await service.conversations.get_owned_conversation(body.conversation_id, user_id)
        await service.prepare_completion_turn(
            conversation_id=body.conversation_id,
            user_id=user_id,
            content=body.content,
            client_message_id=body.client_message_id,
            regenerate=body.regenerate,
        )

        stream_state = service.new_completion_stream_state(
            conversation_id=body.conversation_id,
            user_id=user_id,
        )

    async def event_generator():
        yield f"data: {json.dumps({'event': 'start', 'data': {'stream_id': stream_state.stream_id}}, ensure_ascii=False)}\n\n"

        async with AsyncSessionLocal() as stream_db:
            stream_service = ChatService(stream_db, redis=redis)
            try:
                async for event in stream_service.stream_completion_events(
                    stream_state=stream_state,
                    request=request,
                    skip_start_event=True,
                ):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                assistant_id = await stream_service.finalize_completion_stream(
                    stream_state,
                )
                if assistant_id is not None:
                    done_data: dict = {
                        "message_id": str(assistant_id),
                        "stream_id": stream_state.stream_id,
                    }
                    if stream_state.rag_source_items:
                        done_data["sources"] = stream_state.rag_source_items
                    done_frame = {"event": "done", "data": done_data}
                    yield f"data: {json.dumps(done_frame, ensure_ascii=False)}\n\n"
            finally:
                if not stream_state.persisted:
                    await stream_service.finalize_completion_stream(
                        stream_state,
                    )
                await stream_service.release_turn_inflight_lock(
                    body.conversation_id,
                    body.client_message_id,
                )

    gen = event_generator()
    first_frame = await gen.__anext__()

    async def stream_body():
        yield first_frame
        async for chunk in gen:
            yield chunk

    return StreamingResponse(
        stream_body(),
        media_type="text/event-stream",
        headers={
            "X-Stream-Id": stream_state.stream_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/completions/cancel")
async def chat_completions_cancel(
    body: ChatCancelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    redis: Redis | None = await ensure_redis()
    service = ChatService(db, redis=redis)
    await service.cancel_stream(
        stream_id=str(body.stream_id),
        user_id=user.id,
        visible_content=body.visible_content,
        visible_length=body.visible_length,
    )
    return success()
