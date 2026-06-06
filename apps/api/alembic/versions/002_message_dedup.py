"""messages client_message_id and completion_status

Revision ID: 002
Revises: 001
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("client_message_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("completion_status", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "uq_messages_conversation_client_message_id",
        "messages",
        ["conversation_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_messages_conversation_client_message_id",
        table_name="messages",
    )
    op.drop_column("messages", "completion_status")
    op.drop_column("messages", "client_message_id")
