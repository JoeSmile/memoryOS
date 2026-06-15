from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.worldcup_match_service import WorldcupMatchService


def _match_row(
    match_id: str,
    stage: str,
    match_date: date,
    home: str,
    away: str,
) -> tuple[MagicMock, str, str, str]:
    match = MagicMock()
    match.id = match_id
    match.name = f"{home} vs {away}"
    match.stage_name = stage
    match.group_name = None
    match.match_date = match_date
    match.home_score = 1
    match.away_score = 0
    match.extra_time = False
    match.penalty_shootout = False
    match.home_penalty_score = None
    match.away_penalty_score = None
    return match, home, away, "2022 FIFA Men's World Cup"


@pytest.mark.asyncio
async def test_list_groups_stages_in_date_desc_order():
    repo = MagicMock()
    repo.list_for_tournament = AsyncMock(
        return_value=[
            _match_row("M-2022-64", "final", date(2022, 12, 18), "Argentina", "France"),
            _match_row("M-2022-63", "semi-finals", date(2022, 12, 14), "France", "Morocco"),
            _match_row("M-2022-01", "group stage", date(2022, 11, 20), "Qatar", "Ecuador"),
        ],
    )
    service = WorldcupMatchService(repo)
    result = await service.list_tournament_matches("WC-2022")

    assert result.tournament_id == "WC-2022"
    assert [stage.stage_name for stage in result.stages] == [
        "final",
        "semi-finals",
        "group stage",
    ]
    assert result.stages[0].stage_label == "决赛"
    assert result.stages[0].matches[0].id == "M-2022-64"
