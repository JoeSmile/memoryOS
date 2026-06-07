from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WcPlayerAppearance(Base):
    __tablename__ = "wc_player_appearances"

    match_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("wc_matches.id"),
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
    tournament_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("wc_tournaments.id"),
        nullable=False,
    )
    shirt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    position_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    starter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    substitute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
