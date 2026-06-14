import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rag_constants import EMBEDDING_DIMENSIONS
from app.models.base import Base


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        UniqueConstraint("user_id", "memory_key", name="uq_memories_user_memory_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_key: Mapped[str] = mapped_column(String(128), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        default=Decimal("0.500"),
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="memories")
