"""ep06 memories table and conversation context summary

Revision ID: 014
Revises: 013
Create Date: 2026-06-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Keep in sync with app.core.rag_constants.EMBEDDING_DIMENSIONS
EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "conversations",
        sa.Column("context_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("summary_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "memories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("memory_key", sa.String(length=128), nullable=False),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "importance",
            sa.Numeric(precision=4, scale=3),
            nullable=False,
            server_default="0.500",
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "memory_type IN ('preference', 'fact', 'constraint')",
            name="ck_memories_memory_type",
        ),
        sa.CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_memories_importance_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "memory_key",
            name="uq_memories_user_memory_key",
        ),
    )
    op.create_index(
        op.f("ix_memories_user_id"),
        "memories",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_memories_user_id"), table_name="memories")
    op.drop_table("memories")
    op.drop_column("conversations", "summary_updated_at")
    op.drop_column("conversations", "context_summary")
