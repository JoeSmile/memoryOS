"""Semantic search over ingested document chunks (pgvector cosine)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.knowledge import KnowledgeChunkHit, KnowledgeSearchResult
from app.services.embedding_service import EmbeddingService


def _distance_to_score(distance: float) -> float:
    # pgvector cosine distance: 0 = identical on L2-normalized vectors.
    return 1.0 - distance


class KnowledgeSearchService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        embeddings: EmbeddingService | None = None,
    ) -> None:
        self.chunks = DocumentChunkRepository(db)
        self._embeddings = embeddings or EmbeddingService()

    async def search(
        self,
        query: str,
        *,
        collection: str | None = None,
        top_k: int = 5,
    ) -> KnowledgeSearchResult:
        query_vector = await self._embeddings.embed_query(query)
        rows = await self.chunks.search_similar(
            query_vector,
            top_k=top_k,
            collection=collection,
        )
        hits = [
            KnowledgeChunkHit(
                content=row.chunk.content,
                score=_distance_to_score(row.distance),
                document_id=row.document.id,
                external_id=row.document.external_id,
                entity_type=row.document.entity_type,
                collection=row.document.collection,
            )
            for row in rows
        ]
        return KnowledgeSearchResult(chunks=hits)
