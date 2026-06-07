"""Unit tests for World Cup player ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.players import _player_rows
from app.etl.worldcup.transforms import (
    parse_positions,
    player_display_name,
    split_tournament_years,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


def test_split_tournament_years():
    assert split_tournament_years("1995, 1999") == [1995, 1999]
    assert split_tournament_years("2022") == [2022]
    assert split_tournament_years("") == []


def test_parse_positions_multi():
    positions, primary = parse_positions(
        {
            "goal_keeper": "0",
            "defender": "1",
            "midfielder": "1",
            "forward": "0",
        }
    )
    assert positions == ["DF", "MF"]
    assert primary == "DF"


def test_player_display_name():
    assert player_display_name("Lionel", "Messi") == "Lionel Messi"


def test_parse_optional_date():
    from app.etl.worldcup.transforms import parse_optional_date

    assert parse_optional_date("1934-09-30") is not None
    assert parse_optional_date("not available") is None


@pytest.mark.skipif(
    not (BRONZE_DIR / "players.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_player_rows_full_bronze():
    players, years = _player_rows(BRONZE_DIR)
    assert len(players) == 10401
    assert len(years) > 10401
    for player in players:
        player_years = [y["year"] for y in years if y["player_id"] == player["id"]]
        assert len(player_years) == player["count_tournaments"]

    messi = next((p for p in players if p["given_name"] == "Lionel" and p["family_name"] == "Messi"), None)
    if messi:
        assert messi["primary_position"] == "FW"


def test_brenden_aaronson_fixture_row():
    if not (BRONZE_DIR / "players.csv").is_file():
        pytest.skip("full bronze CSV not available")
    players, years = _player_rows(BRONZE_DIR)
    brenden = next(p for p in players if p["id"] == "P-03484")
    assert brenden["display_name"] == "Brenden Aaronson"
    assert years.count({"player_id": "P-03484", "year": 2022}) == 1
