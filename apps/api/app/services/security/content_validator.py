from app.core.config import settings
from app.core.exceptions import AppException


def assert_chat_content_length(
    content: str,
    *,
    max_chars: int | None = None,
) -> None:
    """Reject user-visible chat/demo text before LLM or demo-turn persist."""
    limit = settings.chat_max_content_chars if max_chars is None else max_chars
    if len(content) > limit:
        raise AppException(
            code=42201,
            message="content_too_long",
            status_code=422,
        )
