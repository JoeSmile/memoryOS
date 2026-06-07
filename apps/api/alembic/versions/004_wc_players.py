"""wc players and player_tournament_years

Revision ID: 004
Revises: 003
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_players",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("family_name", sa.String(length=200), nullable=False),
        sa.Column("given_name", sa.String(length=200), nullable=False),
        sa.Column("display_name", sa.String(length=400), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("female", sa.Boolean(), nullable=False),
        sa.Column(
            "positions",
            postgresql.ARRAY(sa.String(length=4)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("primary_position", sa.String(length=4), nullable=True),
        sa.Column("count_tournaments", sa.Integer(), nullable=False),
        sa.Column("wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "wc_player_tournament_years",
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("player_id", "year"),
    )
    op.create_index(
        op.f("ix_wc_player_tournament_years_year"),
        "wc_player_tournament_years",
        ["year"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_wc_player_tournament_years_year"),
        table_name="wc_player_tournament_years",
    )
    op.drop_table("wc_player_tournament_years")
    op.drop_table("wc_players")
