"""rag document_chunks embedding vector(1024) for Bailian text-embedding-v4

Revision ID: 012
Revises: 011
Create Date: 2026-06-07

Ensures vector(1024) after 011 (legacy 384 or fresh 1024). Clears chunks;
full re-ingest required when upgrading from 384.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM document_chunks")
    op.execute(
        "ALTER TABLE document_chunks "
        "ALTER COLUMN embedding TYPE vector(1024)"
    )


def downgrade() -> None:
    op.execute("DELETE FROM document_chunks")
    op.execute(
        "ALTER TABLE document_chunks "
        "ALTER COLUMN embedding TYPE vector(384)"
    )
