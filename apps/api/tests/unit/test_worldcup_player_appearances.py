"""Unit tests for World Cup player appearance ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.player_appearances import _player_appearance_rows

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


@pytest.mark.skipif(
    not (BRONZE_DIR / "player_appearances.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_player_appearance_rows():
    rows = _player_appearance_rows(BRONZE_DIR)
    assert len(rows) == 27432

    keys = {(r["match_id"], r["team_id"], r["player_id"]) for r in rows}
    assert len(keys) == 27432

    assert all(row["starter"] ^ row["substitute"] for row in rows)

    wc2022 = [r for r in rows if r["tournament_id"] == "WC-2022"]
    assert len(wc2022) == 1995
    starters = sum(1 for r in wc2022 if r["starter"])
    assert 0 < starters < len(wc2022)
