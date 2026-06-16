"""RAG chunk sanitization — shared by ETL ingest and retrieve (no FastAPI imports)."""

import unicodedata
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings
from app.schemas.knowledge import KnowledgeChunkHit
from app.services.security.content_provenance import (
    provenance_for_collection,
    shield_text_for_provenance,
)
from app.services.security.injection_patterns import neutralize_override_phrases

# Keep newlines/tabs for readable fact-card text; strip other C0 controls.
_ALLOWED_WHITESPACE = frozenset("\n\t\r")


class ChunkSanitizer(Protocol):
    def sanitize(self, text: str) -> str:
        """Return text safe to embed or inject into `<DOCS>`."""
        ...


def _strip_control_chars(text: str) -> str:
    return "".join(
        ch
        for ch in text
        if ch in _ALLOWED_WHITESPACE or unicodedata.category(ch) != "Cc"
    )


def sanitize_chunk(
    text: str,
    *,
    max_chars: int | None = None,
) -> str:
    """Normalize, strip controls, neutralize override phrases, enforce length."""
    limit = settings.rag_chunk_max_chars if max_chars is None else max_chars
    cleaned = _strip_control_chars(text)
    cleaned = neutralize_override_phrases(cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[:limit]
    return cleaned


def sanitize_knowledge_chunk(hit: KnowledgeChunkHit) -> KnowledgeChunkHit:
    """Sanitize a retrieve hit before graph state or prompt assembly."""
    return hit.model_copy(update={"content": sanitize_chunk(hit.content)})


def sanitize_retrieved_knowledge_chunk(hit: KnowledgeChunkHit) -> KnowledgeChunkHit:
    """Retrieve path: rule-based L1, then EntropyShield only for untrusted collections."""
    provenance = provenance_for_collection(hit.collection)
    content = sanitize_chunk(hit.content)
    content = shield_text_for_provenance(content, provenance)
    return hit.model_copy(update={"content": content})


@dataclass(frozen=True)
class RuleBasedChunkSanitizer:
    """Default L1 sanitizer; optional adapters (e.g. EntropyShield) wrap this."""

    max_chars: int | None = None

    def sanitize(self, text: str) -> str:
        return sanitize_chunk(text, max_chars=self.max_chars)


def default_chunk_sanitizer() -> RuleBasedChunkSanitizer:
    return RuleBasedChunkSanitizer()
