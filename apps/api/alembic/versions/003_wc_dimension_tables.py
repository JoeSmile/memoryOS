"""wc dimension tables confederations teams tournaments stadiums

Revision ID: 003
Revises: 002
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wc_confederations",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
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
        "wc_teams",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("mens_team", sa.Boolean(), nullable=False),
        sa.Column("womens_team", sa.Boolean(), nullable=False),
        sa.Column("federation_name", sa.String(length=200), nullable=True),
        sa.Column("region_name", sa.String(length=100), nullable=True),
        sa.Column("confederation_id", sa.String(length=16), nullable=False),
        sa.Column("mens_team_wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column("womens_team_wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column("federation_wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["confederation_id"],
            ["wc_confederations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_wc_teams_confederation_id"),
        "wc_teams",
        ["confederation_id"],
        unique=False,
    )
    op.create_table(
        "wc_tournaments",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("host_country", sa.String(length=100), nullable=True),
        sa.Column("winner", sa.String(length=100), nullable=True),
        sa.Column("host_won", sa.Boolean(), nullable=False),
        sa.Column("count_teams", sa.Integer(), nullable=True),
        sa.Column("group_stage", sa.Boolean(), nullable=False),
        sa.Column("second_group_stage", sa.Boolean(), nullable=False),
        sa.Column("final_round", sa.Boolean(), nullable=False),
        sa.Column("round_of_16", sa.Boolean(), nullable=False),
        sa.Column("quarter_finals", sa.Boolean(), nullable=False),
        sa.Column("semi_finals", sa.Boolean(), nullable=False),
        sa.Column("third_place_match", sa.Boolean(), nullable=False),
        sa.Column("final", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "wc_stadiums",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("city_name", sa.String(length=100), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("stadium_wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column("city_wikipedia_link", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("wc_stadiums")
    op.drop_table("wc_tournaments")
    op.drop_index(op.f("ix_wc_teams_confederation_id"), table_name="wc_teams")
    op.drop_table("wc_teams")
    op.drop_table("wc_confederations")
