from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

POSITION_CODES = ("GK", "DF", "MF", "FW")


class WcPlayer(Base):
    __tablename__ = "wc_players"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    family_name: Mapped[str] = mapped_column(String(200), nullable=False)
    given_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(400), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    female: Mapped[bool] = mapped_column(nullable=False, default=False)
    positions: Mapped[list[str]] = mapped_column(
        ARRAY(String(4)),
        nullable=False,
        server_default="{}",
    )
    primary_position: Mapped[str | None] = mapped_column(String(4), nullable=True)
    count_tournaments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wikipedia_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    tournament_years: Mapped[list["WcPlayerTournamentYear"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )


class WcPlayerTournamentYear(Base):
    __tablename__ = "wc_player_tournament_years"

    player_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_players.id", ondelete="CASCADE"),
        primary_key=True,
    )
    year: Mapped[int] = mapped_column(Integer, primary_key=True)

    player: Mapped["WcPlayer"] = relationship(back_populates="tournament_years")
