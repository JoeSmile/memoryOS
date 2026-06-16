from app.core.config import settings
from app.core.exceptions import AppException
from app.services.security.injection_patterns import contains_override_phrase


def contains_prompt_injection(text: str) -> bool:
    return contains_override_phrase(text)


def assert_user_input_safe(content: str) -> None:
    """Reject obvious prompt-injection phrases before LLM or graph invocation.

    Scope: high-confidence EN/ZH override phrases only (L0 heuristic).
    Other languages / indirect jailbreaks are covered by rag_sanitizer (2.3+),
    POLICY/DOCS (2.6), and optional LLM Guard ML (2.9).
    """
    if not settings.prompt_injection_filter_enabled:
        return
    if contains_prompt_injection(content):
        raise AppException(
            code=42201,
            message="prompt_injection_detected",
            status_code=422,
        )
