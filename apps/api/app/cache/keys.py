import uuid


def conversation_list_key(user_id: uuid.UUID) -> str:
    return f"memoryos:conversations:user:{user_id}"


def stream_key(conversation_id: uuid.UUID, stream_id: str) -> str:
    return f"memoryos:stream:{conversation_id}:{stream_id}"
