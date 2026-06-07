"""Unit tests for World Cup standings, awards, and referee ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.standings_refs import (
    _award_rows,
    _award_winner_rows,
    _group_standing_rows,
    _qualified_team_rows,
    _referee_appearance_rows,
    _referee_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


@pytest.mark.skipif(
    not (BRONZE_DIR / "group_standings.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_standings_refs_rows():
    assert len(_award_rows(BRONZE_DIR)) == 8
    assert len(_award_winner_rows(BRONZE_DIR)) == 200
    assert len(_qualified_team_rows(BRONZE_DIR)) == 625
    assert len(_group_standing_rows(BRONZE_DIR)) == 626
    assert len(_referee_rows(BRONZE_DIR)) == 493
    assert len(_referee_appearance_rows(BRONZE_DIR)) == 1248

    wc2022_q = [r for r in _qualified_team_rows(BRONZE_DIR) if r["tournament_id"] == "WC-2022"]
    assert len(wc2022_q) == 32

    wc2022_gs = [r for r in _group_standing_rows(BRONZE_DIR) if r["tournament_id"] == "WC-2022"]
    assert len(wc2022_gs) == 32
    assert sum(1 for r in wc2022_gs if r["advanced"]) == 16

    golden_boot = [
        r
        for r in _award_winner_rows(BRONZE_DIR)
        if r["tournament_id"] == "WC-2022" and r["award_id"] == "A-4"
    ]
    assert len(golden_boot) == 1
