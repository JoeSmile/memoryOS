"""wc substitutions penalty kicks

Revision ID: 007
Revises: 006
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_substitutions",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("minute_regulation", sa.Integer(), nullable=False),
        sa.Column("minute_stoppage", sa.Integer(), nullable=False),
        sa.Column("match_period", sa.String(length=64), nullable=False),
        sa.Column("going_off", sa.Boolean(), nullable=False),
        sa.Column("coming_on", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["wc_matches.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "wc_penalty_kicks",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("converted", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["wc_matches.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("wc_penalty_kicks")
    op.drop_table("wc_substitutions")
