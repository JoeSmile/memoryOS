import uuid


def conversation_list_key(user_id: uuid.UUID) -> str:
    return f"memoryos:conversations:user:{user_id}"


def stream_key(conversation_id: uuid.UUID, stream_id: str) -> str:
    return f"memoryos:stream:{conversation_id}:{stream_id}"


def completion_turn_inflight_key(
    conversation_id: uuid.UUID,
    client_message_id: uuid.UUID,
) -> str:
    return f"memoryos:completion_inflight:{conversation_id}:{client_message_id}"
