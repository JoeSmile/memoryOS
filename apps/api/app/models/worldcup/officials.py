from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WcReferee(Base):
    __tablename__ = "wc_referees"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    family_name: Mapped[str] = mapped_column(String(200), nullable=False)
    given_name: Mapped[str] = mapped_column(String(200), nullable=False)
    female: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    country_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confederation_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_confederations.id"),
        nullable=False,
    )
    wikipedia_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )


class WcRefereeAppearance(Base):
    __tablename__ = "wc_referee_appearances"

    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
        primary_key=True,
    )
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    referee_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_referees.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
