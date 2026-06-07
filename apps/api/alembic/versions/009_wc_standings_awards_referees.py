"""wc standings awards referees

Revision ID: 009
Revises: 008
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_awards",
        sa.Column("id", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("year_introduced", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "wc_referees",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("family_name", sa.String(length=200), nullable=False),
        sa.Column("given_name", sa.String(length=200), nullable=False),
        sa.Column("female", sa.Boolean(), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=True),
        sa.Column("confederation_id", sa.String(length=16), nullable=False),
        sa.Column("wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["confederation_id"], ["wc_confederations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "wc_award_winners",
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("award_id", sa.String(length=8), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("shared", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["award_id"], ["wc_awards.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("tournament_id", "award_id", "player_id"),
    )
    op.create_table(
        "wc_qualified_teams",
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("count_matches", sa.Integer(), nullable=False),
        sa.Column("performance", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("tournament_id", "team_id"),
    )
    op.create_table(
        "wc_group_standings",
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("stage_number", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(length=32), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("stage_name", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("played", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("draws", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("goals_for", sa.Integer(), nullable=False),
        sa.Column("goals_against", sa.Integer(), nullable=False),
        sa.Column("goal_difference", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("advanced", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("tournament_id", "stage_number", "group_name", "team_id"),
    )
    op.create_table(
        "wc_referee_appearances",
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("referee_id", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["wc_matches.id"]),
        sa.ForeignKeyConstraint(["referee_id"], ["wc_referees.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("match_id"),
    )


def downgrade() -> None:
    op.drop_table("wc_referee_appearances")
    op.drop_table("wc_group_standings")
    op.drop_table("wc_qualified_teams")
    op.drop_table("wc_award_winners")
    op.drop_table("wc_referees")
    op.drop_table("wc_awards")
