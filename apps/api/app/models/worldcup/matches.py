from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WcMatch(Base):
    __tablename__ = "wc_matches"

    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    group_stage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    knockout_stage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_replayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_replay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    replay_of_match_id: Mapped[str | None] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        nullable=True,
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    match_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    stadium_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_stadiums.id"),
        nullable=False,
    )
    home_team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    away_team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    extra_time: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    penalty_shootout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    home_penalty_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_penalty_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    team_stats: Mapped[list["WcTeamMatchStat"]] = relationship(back_populates="match")


class WcTeamMatchStat(Base):
    __tablename__ = "wc_team_match_stats"

    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        primary_key=True,
    )
    opponent_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_teams.id"),
        nullable=False,
    )
    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_differential: Mapped[int] = mapped_column(Integer, nullable=False)
    extra_time: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    penalty_shootout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    penalties_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    penalties_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    won: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    drew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    match: Mapped["WcMatch"] = relationship(back_populates="team_stats")
