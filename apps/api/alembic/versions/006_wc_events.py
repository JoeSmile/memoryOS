"""wc goals squads bookings

Revision ID: 006
Revises: 005
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_goals",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("player_team_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("minute_regulation", sa.Integer(), nullable=False),
        sa.Column("minute_stoppage", sa.Integer(), nullable=False),
        sa.Column("match_period", sa.String(length=64), nullable=False),
        sa.Column("own_goal", sa.Boolean(), nullable=False),
        sa.Column("penalty", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["wc_matches.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"]),
        sa.ForeignKeyConstraint(["player_team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wc_goals_match_id"), "wc_goals", ["match_id"], unique=False)
    op.create_table(
        "wc_squads",
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("position_name", sa.String(length=64), nullable=True),
        sa.Column("position_code", sa.String(length=8), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["wc_players.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["wc_teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["wc_tournaments.id"]),
        sa.PrimaryKeyConstraint("tournament_id", "team_id", "player_id"),
    )
    op.create_table(
        "wc_bookings",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("tournament_id", sa.String(length=16), nullable=False),
        sa.Column("match_id", sa.String(length=24), nullable=False),
        sa.Column("team_id", sa.String(length=16), nullable=False),
        sa.Column("player_id", sa.String(length=16), nullable=False),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("minute_regulation", sa.Integer(), nullable=False),
        sa.Column("minute_stoppage", sa.Integer(), nullable=False),
        sa.Column("match_period", sa.String(length=64), nullable=False),
        sa.Column("yellow_card", sa.Boolean(), nullable=False),
        sa.Column("red_card", sa.Boolean(), nullable=False),
        sa.Column("second_yellow_card", sa.Boolean(), nullable=False),
        sa.Column("sending_off", sa.Boolean(), nullable=False),
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
    op.create_index(
        op.f("ix_wc_bookings_match_id"), "wc_bookings", ["match_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_wc_bookings_match_id"), table_name="wc_bookings")
    op.drop_table("wc_bookings")
    op.drop_table("wc_squads")
    op.drop_index(op.f("ix_wc_goals_match_id"), table_name="wc_goals")
    op.drop_table("wc_goals")
