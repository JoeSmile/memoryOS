import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryRead


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.memories = MemoryRepository(db)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryRead]:
        rows = await self.memories.list_by_user_id(
            user_id,
            limit=limit,
            offset=offset,
        )
        return [MemoryRead.model_validate(row) for row in rows]

    async def delete_for_user(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        memory = await self.memories.get_by_id_for_user(memory_id, user_id)
        if memory is None:
            raise AppException(
                code=40401,
                message="memory_not_found",
                status_code=404,
            )
        await self.memories.delete_by_id(memory_id)
