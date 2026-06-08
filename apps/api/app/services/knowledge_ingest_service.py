"""World Cup Gold fact-card ingest into documents / document_chunks."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION_STEMS: tuple[str, ...] = (
    "matches",
    "players",
    "player_careers",
    "tournaments",
    "samples",
)
COLLECTION_PREFIX = "worldcup"
EMBED_BATCH_SIZE = 10
EMBED_RETRY_DELAYS_SEC = (1.0, 2.0, 4.0)
LIVE_BATCH_SLEEP_SEC = 0.5


class KnowledgeIngestError(Exception):
    """Batch embed or IO failed; caller should exit non-zero."""

    def __init__(
        self,
        message: str,
        *,
        collection: str,
        external_ids: list[str],
    ) -> None:
        super().__init__(message)
        self.collection = collection
        self.external_ids = external_ids


@dataclass
class IngestCollectionResult:
    stem: str
    collection: str
    lines_read: int = 0
    documents_created: int = 0
    documents_updated: int = 0


@dataclass
class KnowledgeIngestSummary:
    collections: list[IngestCollectionResult] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return sum(item.lines_read for item in self.collections)


def collection_name(stem: str) -> str:
    return f"{COLLECTION_PREFIX}-{stem}"


def default_gold_fact_cards_dir() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "data"
        / "gold"
        / "worldcup"
        / "fact_cards"
    )


class KnowledgeIngestService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        embeddings: EmbeddingService | None = None,
        gold_dir: Path | None = None,
    ) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.chunks = DocumentChunkRepository(db)
        self._embeddings = embeddings or EmbeddingService()
        self._gold_dir = gold_dir or default_gold_fact_cards_dir()

    async def ingest_worldcup_fact_cards(
        self,
        collection_stems: list[str] | None = None,
    ) -> KnowledgeIngestSummary:
        stems = collection_stems or list(DEFAULT_COLLECTION_STEMS)
        summary = KnowledgeIngestSummary()

        for stem in stems:
            path = self._gold_dir / f"{stem}.jsonl"
            if not path.is_file():
                raise KnowledgeIngestError(
                    f"missing gold file: {path}",
                    collection=collection_name(stem),
                    external_ids=[],
                )
            result = await self._ingest_file(stem=stem, path=path)
            summary.collections.append(result)
            await self.db.commit()

        return summary

    async def _ingest_file(self, *, stem: str, path: Path) -> IngestCollectionResult:
        collection = collection_name(stem)
        result = IngestCollectionResult(stem=stem, collection=collection)
        batch_rows: list[dict[str, Any]] = []

        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                batch_rows.append(json.loads(line))
                if len(batch_rows) >= EMBED_BATCH_SIZE:
                    created, updated = await self._ingest_batch(collection, batch_rows)
                    result.lines_read += len(batch_rows)
                    result.documents_created += created
                    result.documents_updated += updated
                    batch_rows = []
                    await self._sleep_between_batches()

            if batch_rows:
                created, updated = await self._ingest_batch(collection, batch_rows)
                result.lines_read += len(batch_rows)
                result.documents_created += created
                result.documents_updated += updated

        logger.info(
            "ingested %s: lines=%s created=%s updated=%s",
            collection,
            result.lines_read,
            result.documents_created,
            result.documents_updated,
        )
        return result

    async def _ingest_batch(
        self,
        collection: str,
        rows: list[dict[str, Any]],
    ) -> tuple[int, int]:
        external_ids = [row["id"] for row in rows]
        texts = [row["text"] for row in rows]
        vectors = await self._embed_batch_with_retry(
            texts,
            collection=collection,
            external_ids=external_ids,
        )

        created = 0
        updated = 0
        for row, vector in zip(rows, vectors, strict=True):
            document, is_new = await self.documents.upsert(
                collection=collection,
                external_id=row["id"],
                entity_type=row.get("entity_type"),
                source_ids=row.get("source_ids"),
                metadata=None,
            )
            await self.chunks.replace_for_document(
                document_id=document.id,
                chunk_index=0,
                content=row["text"],
                embedding=vector,
            )
            if is_new:
                created += 1
            else:
                updated += 1

        return created, updated

    async def _embed_batch_with_retry(
        self,
        texts: list[str],
        *,
        collection: str,
        external_ids: list[str],
    ) -> list[list[float]]:
        last_exc: Exception | None = None
        for attempt, delay in enumerate(EMBED_RETRY_DELAYS_SEC, start=1):
            try:
                return await self._embeddings.embed_texts(texts)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "embed batch failed collection=%s attempt=%s ids=%s: %s",
                    collection,
                    attempt,
                    external_ids,
                    exc,
                )
                if attempt < len(EMBED_RETRY_DELAYS_SEC):
                    await asyncio.sleep(delay)

        raise KnowledgeIngestError(
            f"embedding failed after {len(EMBED_RETRY_DELAYS_SEC)} attempts: {last_exc}",
            collection=collection,
            external_ids=external_ids,
        )

    async def _sleep_between_batches(self) -> None:
        if not self._embeddings.use_mock:
            await asyncio.sleep(LIVE_BATCH_SLEEP_SEC)
