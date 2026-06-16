"""Content provenance — trust model for RAG chunks and tool outputs (EP09 2.10+)."""

from enum import StrEnum

# Fixed WC ETL collections (see docs/tech/rag-embedding-chunking.md).
_TRUSTED_COLLECTION_PREFIX = "worldcup-"
_CRAWLER_COLLECTION_PREFIX = "crawler-"
_USER_UPLOAD_COLLECTION_PREFIX = "user-upload-"


class ContentProvenance(StrEnum):
    """Where text entered the system — drives optional DeSyntax (EntropyShield)."""

    TRUSTED_ETL = "trusted_etl"
    WEB_SEARCH = "web_search"
    CRAWLER = "crawler"
    USER_UPLOAD = "user_upload"


_UNTRUSTED: frozenset[ContentProvenance] = frozenset(
    {
        ContentProvenance.WEB_SEARCH,
        ContentProvenance.CRAWLER,
        ContentProvenance.USER_UPLOAD,
    }
)


def is_untrusted(provenance: ContentProvenance) -> bool:
    return provenance in _UNTRUSTED


def provenance_for_collection(collection: str) -> ContentProvenance:
    """Map vector collection name to trust level.

    - ``worldcup-*`` — fixed in-repo ETL (high trust)
    - ``crawler-*`` — future scraped player/match feeds (low trust)
    - ``user-upload-*`` — future user documents (low trust)
    - unknown — default **crawler** (fail-safe for new collections)
    """
    name = collection.strip().lower()
    if name.startswith(_TRUSTED_COLLECTION_PREFIX):
        return ContentProvenance.TRUSTED_ETL
    if name.startswith(_CRAWLER_COLLECTION_PREFIX):
        return ContentProvenance.CRAWLER
    if name.startswith(_USER_UPLOAD_COLLECTION_PREFIX):
        return ContentProvenance.USER_UPLOAD
    return ContentProvenance.CRAWLER


def shield_text_for_provenance(text: str, provenance: ContentProvenance) -> str:
    """Apply EntropyShield only when master switch is on and provenance is untrusted."""
    if not is_untrusted(provenance):
        return text
    from app.services.security.entropyshield_adapter import apply_entropyshield

    return apply_entropyshield(text, provenance=provenance)
