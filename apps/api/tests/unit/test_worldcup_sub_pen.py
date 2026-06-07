"""Unit tests for World Cup substitution / penalty kick ETL."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.etl.worldcup.loaders.sub_pen import _penalty_kick_rows, _substitution_rows

REPO_ROOT = Path(__file__).resolve().parents[4]
BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"


@pytest.mark.skipif(
    not (BRONZE_DIR / "substitutions.csv").is_file(),
    reason="full bronze CSV not available",
)
def test_full_bronze_sub_pen_rows():
    subs = _substitution_rows(BRONZE_DIR)
    pks = _penalty_kick_rows(BRONZE_DIR)
    assert len(subs) == 10222
    assert len(pks) == 396

    assert all(row["going_off"] ^ row["coming_on"] for row in subs)
    assert sum(1 for row in pks if row["converted"]) > 0

    wc2022_pk = [row for row in pks if row["tournament_id"] == "WC-2022"]
    assert 20 < len(wc2022_pk) < 50
