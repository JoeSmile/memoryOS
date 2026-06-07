"""Unit tests for World Cup event ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.events import _booking_rows, _goal_rows, _squad_rows
from app.etl.worldcup.transforms import parse_shirt_number

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


def test_parse_shirt_number():
    assert parse_shirt_number("10") == 10
    assert parse_shirt_number("0") is None
    assert parse_shirt_number("") is None


@pytest.mark.skipif(
    not (BRONZE_DIR / "goals.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_event_rows():
    goals = _goal_rows(BRONZE_DIR)
    squads = _squad_rows(BRONZE_DIR)
    bookings = _booking_rows(BRONZE_DIR)
    assert len(goals) == 3637
    assert len(squads) == 13843
    assert len(bookings) == 3178

    own_goals = [g for g in goals if g["own_goal"]]
    assert len(own_goals) == 79
    assert any(
        g["team_id"] != g["player_team_id"] for g in own_goals
    )

    wc2022_squads = [s for s in squads if s["tournament_id"] == "WC-2022"]
    assert 800 < len(wc2022_squads) < 900
