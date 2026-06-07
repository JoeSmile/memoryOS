"""Unit tests for World Cup dimension transforms and row builders."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.dimensions import (
    _confederation_rows,
    _stadium_rows,
    _team_rows,
    _tournament_rows,
)
from app.etl.worldcup.transforms import clean_url, parse_bool, tournament_slug

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_DIR = REPO_ROOT / "scripts" / "etl" / "worldcup" / "fixtures"
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


def test_tournament_slug():
    assert tournament_slug("WC-2022") == "wc2022"
    assert tournament_slug("WC-2019") == "wc2019"


def test_clean_url():
    assert clean_url("not applicable") is None
    assert clean_url("") is None
    assert clean_url("https://example.com") == "https://example.com"


def test_parse_bool():
    assert parse_bool("1") is True
    assert parse_bool("0") is False
    assert parse_bool(None) is False


def test_team_rows_from_fixtures():
    rows = _team_rows(FIXTURES_DIR)
    assert len(rows) == 2
    assert rows[0]["id"] == "T-01"
    assert rows[0]["code"] == "ARG"
    assert rows[0]["confederation_id"] == "C-01"


def test_tournament_rows_slug():
    # fixtures lack tournaments; use minimal inline check via bronze if present
    if not (BRONZE_DIR / "tournaments.csv").is_file():
        pytest.skip("full bronze CSV not available")
    rows = _tournament_rows(BRONZE_DIR)
    wc2022 = next(row for row in rows if row["id"] == "WC-2022")
    assert wc2022["slug"] == "wc2022"
    assert wc2022["year"] == 2022


@pytest.mark.skipif(
    not (BRONZE_DIR / "teams.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_row_counts():
    assert len(_confederation_rows(BRONZE_DIR)) == 6
    assert len(_team_rows(BRONZE_DIR)) == 88
    assert len(_tournament_rows(BRONZE_DIR)) == 30
    assert len(_stadium_rows(BRONZE_DIR)) == 240


@pytest.mark.skipif(
    not (BRONZE_DIR / "teams.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_team_wiki_cleaned():
    rows = _team_rows(BRONZE_DIR)
    algeria = next(row for row in rows if row["id"] == "T-01")
    assert algeria["womens_team_wikipedia_link"] is None
