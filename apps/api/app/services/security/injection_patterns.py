"""Shared override-phrase patterns for user-input rejection and RAG neutralization."""

import re
import unicodedata

# Zero-width / bidi chars sometimes hide override phrases from naive scans.
INVISIBLE_CHARS = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]"
)

# High-confidence override phrases; avoid bare 忽略/无视 (football analysis uses those in context).
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
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

_NEUTRALIZED_PLACEHOLDER = "[redacted]"


def normalize_for_scan(text: str) -> str:
    cleaned = INVISIBLE_CHARS.sub("", text)
    return unicodedata.normalize("NFKC", cleaned)


def contains_override_phrase(text: str) -> bool:
    normalized = normalize_for_scan(text)
    return any(pattern.search(normalized) for pattern in INJECTION_PATTERNS)


def neutralize_override_phrases(text: str) -> str:
    """Replace override phrases with a neutral placeholder (RAG / ETL path)."""
    result = normalize_for_scan(text)
    for pattern in INJECTION_PATTERNS:
        result = pattern.sub(_NEUTRALIZED_PLACEHOLDER, result)
    return result
