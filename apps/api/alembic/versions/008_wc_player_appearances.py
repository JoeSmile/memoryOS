"""wc player appearances

Revision ID: 008
Revises: 007
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_player_appearances",
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("position_name", sa.String(length=64), nullable=True),
        sa.Column("position_code", sa.String(length=8), nullable=True),
        sa.Column("starter", sa.Boolean(), nullable=False),
        sa.Column("substitute", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("match_id", "team_id", "player_id"),
    )


def downgrade() -> None:
    op.drop_table("wc_player_appearances")
