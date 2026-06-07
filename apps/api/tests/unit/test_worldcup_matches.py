"""Unit tests for World Cup match ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.matches import (
    _link_replay_of,
    _match_rows,
    _team_stat_rows,
    _validate_team_stats,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


def test_link_replay_of_pair():
    rows = [
        {
            "id": "M-1934-12",
            "tournament_id": "WC-1934",
            "name": "Italy vs Spain",
            "is_replayed": True,
            "is_replay": False,
            "replay_of_match_id": None,
        },
        {
            "id": "M-1934-13",
            "tournament_id": "WC-1934",
            "name": "Italy vs Spain",
            "is_replayed": False,
            "is_replay": True,
            "replay_of_match_id": None,
        },
    ]
    _link_replay_of(rows)
    assert rows[1]["replay_of_match_id"] == "M-1934-12"


@pytest.mark.skipif(
    not (BRONZE_DIR / "matches.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_match_rows():
    matches = _match_rows(BRONZE_DIR)
    stats = _team_stat_rows(BRONZE_DIR)
    assert len(matches) == 1248
    assert len(stats) == 2496
    _validate_team_stats(matches, stats)

    replay = next(m for m in matches if m["id"] == "M-1934-13")
    assert replay["is_replay"] is True
    assert replay["replay_of_match_id"] == "M-1934-12"

    wc2022_final = next(m for m in matches if m["id"] == "M-2022-64")
    assert wc2022_final["home_score"] == 3
    assert wc2022_final["away_score"] == 3
    assert wc2022_final["penalty_shootout"] is True


@pytest.mark.skipif(
    not (BRONZE_DIR / "matches.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_team_stats_two_rows_per_match():
    stats = _team_stat_rows(BRONZE_DIR)
    from collections import Counter

    counts = Counter(s["match_id"] for s in stats)
    assert all(count == 2 for count in counts.values())
    assert len(counts) == 1248
