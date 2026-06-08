from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.core.response import success
from app.models import User
from app.schemas.knowledge import (
    KnowledgeIngestCollectionData,
    KnowledgeIngestData,
    KnowledgeIngestRequest,
    KnowledgeSearchRequest,
)
from app.services.knowledge_ingest_service import (
    DEFAULT_COLLECTION_STEMS,
    KnowledgeIngestError,
    KnowledgeIngestInProgressError,
    KnowledgeIngestService,
    KnowledgeIngestSummary,
)
from app.services.knowledge_search_service import KnowledgeSearchService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _ingest_summary_data(summary: KnowledgeIngestSummary) -> dict:
    data = KnowledgeIngestData(
        total_lines=summary.total_lines,
        collections=[
            KnowledgeIngestCollectionData(
                collection=item.collection,
                lines_read=item.lines_read,
                documents_created=item.documents_created,
                documents_updated=item.documents_updated,
                documents_skipped=item.documents_skipped,
            )
            for item in summary.collections
        ],
    )
    return data.model_dump()


@router.post("/search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeSearchService(db)
    result = await service.search(
        body.query,
        collection=body.collection,
        top_k=body.top_k,
    )
    return success(data=result.model_dump(mode="json"))


@router.post("/ingest/worldcup")
async def ingest_worldcup_knowledge(
    body: KnowledgeIngestRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
):
    stems = body.collections
    if stems is not None:
        allowed = set(DEFAULT_COLLECTION_STEMS)
        unknown = [stem for stem in stems if stem not in allowed]
        if unknown:
            raise AppException(
                code=42201,
                message="invalid_collection_stems",
                status_code=422,
            )

    service = KnowledgeIngestService(db, redis=redis)
    try:
        summary = await service.ingest_worldcup_fact_cards(stems)
    except KnowledgeIngestInProgressError as exc:
        raise AppException(
            code=40902,
            message="ingest_in_progress",
            status_code=409,
        ) from exc
    except KnowledgeIngestError as exc:
        raise AppException(
            code=50001,
            message="ingest_failed",
            status_code=500,
        ) from exc

    return success(data=_ingest_summary_data(summary))
