import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Document, DocumentChunk


@dataclass(frozen=True)
class SimilarChunkRow:
    chunk: DocumentChunk
    document: Document
    distance: float


class DocumentChunkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def delete_by_document_id(self, document_id: uuid.UUID) -> None:
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

    async def create(
        self,
        *,
        document_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        token_count: int | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            token_count=token_count,
        )
        self.db.add(chunk)
        await self.db.flush()
        await self.db.refresh(chunk)
        return chunk

    async def replace_for_document(
        self,
        *,
        document_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        token_count: int | None = None,
    ) -> DocumentChunk:
        """Re-ingest: drop old vectors then insert the new chunk (V1 one chunk per document)."""
        await self.delete_by_document_id(document_id)
        return await self.create(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            token_count=token_count,
        )

    async def search_similar(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        collection: str | None = None,
    ) -> list[SimilarChunkRow]:
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        stmt = (
            select(DocumentChunk, Document, distance_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .order_by(distance_expr)
            .limit(top_k)
        )
        if collection is not None:
            stmt = stmt.where(Document.collection == collection)

        result = await self.db.execute(stmt)
        return [
            SimilarChunkRow(chunk=row[0], document=row[1], distance=float(row[2]))
            for row in result.all()
        ]
