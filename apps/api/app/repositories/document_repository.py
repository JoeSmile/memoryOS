import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_collection_external_id(
        self,
        collection: str,
        external_id: str,
    ) -> Document | None:
        result = await self.db.execute(
            select(Document).where(
                Document.collection == collection,
                Document.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_collection(self, collection: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Document)
            .where(Document.collection == collection)
        )
        return int(result.scalar_one())

    async def touch_updated_at(self, document_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(updated_at=func.now())
        )

    async def upsert(
        self,
        *,
        collection: str,
        external_id: str,
        entity_type: str | None,
        source_ids: list[str] | None,
        metadata: dict[str, Any] | None,
    ) -> tuple[Document, bool]:
        """Insert or update document; always bumps updated_at on update (re-ingest)."""
        existing = await self.get_by_collection_external_id(collection, external_id)
        if existing is not None:
            existing.entity_type = entity_type
            existing.source_ids = source_ids
            existing.metadata_ = metadata
            await self.touch_updated_at(existing.id)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing, False

        document = Document(
            collection=collection,
            external_id=external_id,
            entity_type=entity_type,
            source_ids=source_ids,
            metadata_=metadata,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document, True
