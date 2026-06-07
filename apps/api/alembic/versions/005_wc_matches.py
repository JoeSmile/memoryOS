"""wc matches and team_match_stats

Revision ID: 005
Revises: 004
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_matches",
        sa.Column("id", sa.String(length=24), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("stage_name", sa.String(length=64), nullable=False),
        sa.Column("group_name", sa.String(length=32), nullable=True),
        sa.Column("group_stage", sa.Boolean(), nullable=False),
        sa.Column("knockout_stage", sa.Boolean(), nullable=False),
        sa.Column("is_replayed", sa.Boolean(), nullable=False),
        sa.Column("is_replay", sa.Boolean(), nullable=False),
        sa.Column("replay_of_match_id", sa.String(length=24), nullable=True),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("match_time", sa.String(length=8), nullable=True),
        sa.Column("stadium_id", sa.String(length=16), nullable=False),
        sa.Column("home_team_id", sa.String(length=16), nullable=False),
        sa.Column("away_team_id", sa.String(length=16), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("extra_time", sa.Boolean(), nullable=False),
        sa.Column("penalty_shootout", sa.Boolean(), nullable=False),
        sa.Column("home_penalty_score", sa.Integer(), nullable=True),
        sa.Column("away_penalty_score", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["away_team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["replay_of_match_id"], ["wc_matches.id"]),
        sa.ForeignKeyConstraint(["stadium_id"], ["wc_stadiums.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_wc_matches_tournament_id"),
        "wc_matches",
        ["tournament_id"],
        unique=False,
    )
    op.create_table(
        "wc_team_match_stats",
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("opponent_id", sa.String(length=16), nullable=False),
        sa.Column("is_home", sa.Boolean(), nullable=False),
        sa.Column("goals_for", sa.Integer(), nullable=False),
        sa.Column("goals_against", sa.Integer(), nullable=False),
        sa.Column("goal_differential", sa.Integer(), nullable=False),
        sa.Column("extra_time", sa.Boolean(), nullable=False),
        sa.Column("penalty_shootout", sa.Boolean(), nullable=False),
        sa.Column("penalties_for", sa.Integer(), nullable=True),
        sa.Column("penalties_against", sa.Integer(), nullable=True),
        sa.Column("won", sa.Boolean(), nullable=False),
        sa.Column("lost", sa.Boolean(), nullable=False),
        sa.Column("drew", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["wc_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opponent_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.PrimaryKeyConstraint("match_id", "team_id"),
    )


def downgrade() -> None:
    op.drop_table("wc_team_match_stats")
    op.drop_index(op.f("ix_wc_matches_tournament_id"), table_name="wc_matches")
    op.drop_table("wc_matches")
