from app.repositories.wc_match_repository import WcMatchRepository
from app.schemas.worldcup import (
    WcMatchBrief,
    WcMatchStageGroup,
    WcTournamentMatchesRead,
)

WC_2022_TOURNAMENT_ID = "WC-2022"

STAGE_LABELS: dict[str, str] = {
    "final": "决赛",
    "third-place match": "三四名决赛",
    "semi-finals": "半决赛",
    "quarter-finals": "1/4 决赛",
    "round of 16": "1/8 决赛",
    "group stage": "小组赛",
}


class WorldcupMatchService:
    def __init__(self, repo: WcMatchRepository) -> None:
        self._repo = repo

    async def list_tournament_matches(
        self,
        tournament_id: str,
    ) -> WcTournamentMatchesRead:
        rows = await self._repo.list_for_tournament(tournament_id)
        if not rows:
            return WcTournamentMatchesRead(
                tournament_id=tournament_id,
                tournament_name="",
                stages=[],
            )

        tournament_name = rows[0][3]
        stages: list[WcMatchStageGroup] = []
        stage_index: dict[str, int] = {}

        for match, home_name, away_name, _ in rows:
            brief = WcMatchBrief(
                id=match.id,
                name=match.name,
                stage_name=match.stage_name,
                group_name=match.group_name,
                match_date=match.match_date,
                home_team_name=home_name,
                away_team_name=away_name,
                home_score=match.home_score,
                away_score=match.away_score,
                extra_time=match.extra_time,
                penalty_shootout=match.penalty_shootout,
                home_penalty_score=match.home_penalty_score,
                away_penalty_score=match.away_penalty_score,
            )
            if match.stage_name not in stage_index:
                stage_index[match.stage_name] = len(stages)
                stages.append(
                    WcMatchStageGroup(
                        stage_name=match.stage_name,
                        stage_label=STAGE_LABELS.get(
                            match.stage_name,
                            match.stage_name,
                        ),
                        matches=[],
                    )
                )
            stages[stage_index[match.stage_name]].matches.append(brief)

        return WcTournamentMatchesRead(
            tournament_id=tournament_id,
            tournament_name=tournament_name,
            stages=stages,
        )
