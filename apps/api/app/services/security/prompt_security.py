import re
import unicodedata

from app.core.config import settings
from app.core.exceptions import AppException

# Zero-width / bidi chars sometimes hide override phrases from naive scans.
_INVISIBLE_CHARS = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]"
)

# High-confidence override phrases; avoid bare 忽略/无视 (football analysis uses those in context).
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s*(?:all\s*)?previous\s*instructions?", re.I),
    re.compile(r"disregard\s*(?:the\s*)?(?:above|previous|prior)", re.I),
    re.compile(r"forget\s*(?:all\s*)?(?:previous|prior)\s*instructions?", re.I),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"system\s+prompt\s*:", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"developer\s+message\s*:", re.I),
    re.compile(
        r"忽略\s*(?:先前|之前|以上|上文|前面|前述)\s*(?:的)?\s*(?:指令|指示|规则|提示|prompt)",
        re.I,
    ),
    re.compile(
        r"无视\s*(?:先前|之前|以上|上文|前面|前述)\s*(?:的)?\s*(?:指令|指示|规则)",
        re.I,
    ),
)


def _normalize_for_scan(text: str) -> str:
    cleaned = _INVISIBLE_CHARS.sub("", text)
    return unicodedata.normalize("NFKC", cleaned)


def contains_prompt_injection(text: str) -> bool:
    normalized = _normalize_for_scan(text)
    return any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS)


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
