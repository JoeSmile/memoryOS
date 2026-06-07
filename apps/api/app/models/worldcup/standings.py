from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WcAward(Base):
    __tablename__ = "wc_awards"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    year_introduced: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcAwardWinner(Base):
    __tablename__ = "wc_award_winners"

    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        primary_key=True,
    )
    award_id: Mapped[str] = mapped_column(
        String(8),
        ForeignKey("wc_awards.id"),
        primary_key=True,
    )
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        primary_key=True,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcQualifiedTeam(Base):
    __tablename__ = "wc_qualified_teams"

    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        primary_key=True,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        primary_key=True,
    )
    count_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    performance: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcGroupStanding(Base):
    __tablename__ = "wc_group_standings"

    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        primary_key=True,
    )
    stage_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_name: Mapped[str] = mapped_column(String(32), primary_key=True)
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        primary_key=True,
    )
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    played: Mapped[int] = mapped_column(Integer, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_difference: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    advanced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
