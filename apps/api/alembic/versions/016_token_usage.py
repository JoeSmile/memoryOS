"""ep09 token_usage table

Revision ID: 016
Revises: 015
Create Date: 2026-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_usage",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("prompt_tokens >= 0", name="ck_token_usage_prompt_tokens_nonneg"),
        sa.CheckConstraint(
            "completion_tokens >= 0",
            name="ck_token_usage_completion_tokens_nonneg",
        ),
        sa.CheckConstraint("total_tokens >= 0", name="ck_token_usage_total_tokens_nonneg"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_token_usage_user_created",
        "token_usage",
        ["user_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        op.f("ix_token_usage_conversation_id"),
        "token_usage",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_token_usage_conversation_id"), table_name="token_usage")
    op.drop_index("idx_token_usage_user_created", table_name="token_usage")
    op.drop_table("token_usage")
