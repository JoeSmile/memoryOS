import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory
from app.schemas.memory import MEMORY_TYPES, MemoryType


class _UnsetType:
    __slots__ = ()


_UNSET = _UnsetType()


@dataclass(frozen=True)
class SimilarMemoryRow:
    memory: Memory
    distance: float


def _validate_memory_type(memory_type: str) -> MemoryType:
    if memory_type not in MEMORY_TYPES:
        allowed = ", ".join(sorted(MEMORY_TYPES))
        raise ValueError(f"invalid memory_type '{memory_type}'; expected one of: {allowed}")
    return memory_type


class MemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.updated_at.desc(), Memory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_id(self, memory_id: uuid.UUID) -> Memory | None:
        result = await self.db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Memory | None:
        result = await self.db.execute(
            select(Memory).where(
                Memory.id == memory_id,
                Memory.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_key(
        self,
        user_id: uuid.UUID,
        memory_key: str,
    ) -> Memory | None:
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.memory_key == memory_key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: uuid.UUID,
        memory_key: str,
        memory_type: str,
        content: str,
        importance: Decimal | float = Decimal("0.500"),
        embedding: list[float] | None = None,
        expires_at: datetime | None | _UnsetType = _UNSET,
    ) -> Memory:
        validated_type = _validate_memory_type(memory_type)
        existing = await self.get_by_user_and_key(user_id, memory_key)
        importance_value = Decimal(str(importance))
        if existing is not None:
            existing.memory_type = validated_type
            existing.content = content
            existing.importance = importance_value
            if embedding is not None:
                existing.embedding = embedding
            if expires_at is not _UNSET:
                existing.expires_at = expires_at
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        resolved_expires_at = None if expires_at is _UNSET else expires_at
        memory = Memory(
            user_id=user_id,
            memory_key=memory_key,
            memory_type=validated_type,
            content=content,
            importance=importance_value,
            embedding=embedding,
            expires_at=resolved_expires_at,
        )
        self.db.add(memory)
        await self.db.flush()
        await self.db.refresh(memory)
        return memory

    async def delete_by_id(self, memory_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Memory).where(Memory.id == memory_id)
        )
        return result.rowcount > 0

    async def search_similar_for_user(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[SimilarMemoryRow]:
        distance_expr = Memory.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        stmt = (
            select(Memory, distance_expr)
            .where(Memory.user_id == user_id)
            .where(Memory.embedding.is_not(None))
            .where(
                or_(
                    Memory.expires_at.is_(None),
                    Memory.expires_at > func.now(),
                )
            )
            .order_by(distance_expr)
            .limit(top_k)
        )
        result = await self.db.execute(stmt)
        return [
            SimilarMemoryRow(memory=row[0], distance=float(row[1]))
            for row in result.all()
        ]
