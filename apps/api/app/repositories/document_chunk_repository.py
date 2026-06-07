import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import DocumentChunk


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
