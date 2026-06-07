from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WcGoal(Base):
    __tablename__ = "wc_goals"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        nullable=False,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        nullable=False,
    )
    player_team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minute_regulation: Mapped[int] = mapped_column(Integer, nullable=False)
    minute_stoppage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_period: Mapped[str] = mapped_column(String(64), nullable=False)
    own_goal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    penalty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcSquad(Base):
    __tablename__ = "wc_squads"

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
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        primary_key=True,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    position_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcSubstitution(Base):
    __tablename__ = "wc_substitutions"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        nullable=False,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        nullable=False,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minute_regulation: Mapped[int] = mapped_column(Integer, nullable=False)
    minute_stoppage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_period: Mapped[str] = mapped_column(String(64), nullable=False)
    going_off: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    coming_on: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcPenaltyKick(Base):
    __tablename__ = "wc_penalty_kicks"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        nullable=False,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        nullable=False,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    converted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcBooking(Base):
    __tablename__ = "wc_bookings"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        nullable=False,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id"),
        nullable=False,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minute_regulation: Mapped[int] = mapped_column(Integer, nullable=False)
    minute_stoppage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_period: Mapped[str] = mapped_column(String(64), nullable=False)
    yellow_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    red_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    second_yellow_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sending_off: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
