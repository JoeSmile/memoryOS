from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    collection: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class KnowledgeChunkHit(BaseModel):
    content: str
    score: float
    document_id: UUID
    external_id: str
    entity_type: str | None
    collection: str


class KnowledgeSearchResult(BaseModel):
    chunks: list[KnowledgeChunkHit]


class KnowledgeIngestRequest(BaseModel):
    collections: list[str] | None = None


class KnowledgeIngestCollectionData(BaseModel):
    collection: str
    lines_read: int
    documents_created: int
    documents_updated: int
    documents_skipped: int = 0


class KnowledgeIngestData(BaseModel):
    total_lines: int
    collections: list[KnowledgeIngestCollectionData]
