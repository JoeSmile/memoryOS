from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.worldcup.dimensions import WcTeam, WcTournament
from app.models.worldcup.matches import WcMatch


class WcMatchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_tournament(
        self,
        tournament_id: str,
    ) -> list[tuple[WcMatch, str, str, str]]:
        """Rows: match, home team name, away team name, tournament name."""
        home_team = aliased(WcTeam)
        away_team = aliased(WcTeam)
        stmt = (
            select(
                WcMatch,
                home_team.name,
                away_team.name,
                WcTournament.name,
            )
            .join(home_team, WcMatch.home_team_id == home_team.id)
            .join(away_team, WcMatch.away_team_id == away_team.id)
            .join(WcTournament, WcMatch.tournament_id == WcTournament.id)
            .where(WcMatch.tournament_id == tournament_id)
            .order_by(WcMatch.match_date.desc(), WcMatch.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.all())

    async def get_for_tournament(
        self,
        tournament_id: str,
        match_id: str,
    ) -> tuple[WcMatch, str, str, str] | None:
        home_team = aliased(WcTeam)
        away_team = aliased(WcTeam)
        stmt = (
            select(
                WcMatch,
                home_team.name,
                away_team.name,
                WcTournament.name,
            )
            .join(home_team, WcMatch.home_team_id == home_team.id)
            .join(away_team, WcMatch.away_team_id == away_team.id)
            .join(WcTournament, WcMatch.tournament_id == WcTournament.id)
            .where(
                WcMatch.tournament_id == tournament_id,
                WcMatch.id == match_id,
            )
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        return row if row is not None else None
