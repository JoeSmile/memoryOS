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


def stream_cancel_key(stream_id: str) -> str:
    return f"memoryos:stream_cancel:{stream_id}"


def stream_active_key(stream_id: str) -> str:
    return f"memoryos:stream_active:{stream_id}"


def stream_cancel_visible_key(stream_id: str) -> str:
    return f"memoryos:stream_cancel_visible:{stream_id}"


def stream_cancel_visible_len_key(stream_id: str) -> str:
    return f"memoryos:stream_cancel_visible_len:{stream_id}"


def worldcup_ingest_stem_lock_key(stem: str) -> str:
    """One in-flight ingest per jsonl stem (subset vs full ingest share stem locks)."""
    return f"memoryos:ingest:worldcup:stem:{stem}"
