from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WcConfederation(Base):
    __tablename__ = "wc_confederations"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    wikipedia_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    teams: Mapped[list["WcTeam"]] = relationship(back_populates="confederation")


class WcTeam(Base):
    __tablename__ = "wc_teams"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    mens_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    womens_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    federation_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    region_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confederation_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_confederations.id"),
        nullable=False,
    )
    mens_team_wikipedia_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    womens_team_wikipedia_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    federation_wikipedia_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    confederation: Mapped["WcConfederation"] = relationship(back_populates="teams")


class WcTournament(Base):
    __tablename__ = "wc_tournaments"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    host_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    winner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    host_won: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    count_teams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_stage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    second_group_stage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    final_round: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    round_of_16: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quarter_finals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    semi_finals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    third_place_match: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcStadium(Base):
    __tablename__ = "wc_stadiums"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stadium_wikipedia_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    city_wikipedia_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
