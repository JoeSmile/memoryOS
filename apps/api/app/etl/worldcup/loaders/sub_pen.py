"""Load World Cup substitutions and penalty kicks from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.loaders.events import _upsert_batches
from app.etl.worldcup.transforms import parse_bool, parse_shirt_number
from app.models.worldcup.events import WcPenaltyKick, WcSubstitution


@dataclass(frozen=True)
class SubPenLoadResult:
    substitutions: int
    penalty_kicks: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _substitution_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "substitutions.csv")
    return [
        {
            "id": row["substitution_id"],
            "tournament_id": row["tournament_id"],
            "match_id": row["match_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "minute_regulation": int(row["minute_regulation"]),
            "minute_stoppage": int(row["minute_stoppage"] or 0),
            "match_period": row["match_period"],
            "going_off": parse_bool(row["going_off"]),
            "coming_on": parse_bool(row["coming_on"]),
        }
        for _, row in df.iterrows()
    ]


def _penalty_kick_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "penalty_kicks.csv")
    return [
        {
            "id": row["penalty_kick_id"],
            "tournament_id": row["tournament_id"],
            "match_id": row["match_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "converted": parse_bool(row["converted"]),
        }
        for _, row in df.iterrows()
    ]


async def load_sub_pen(session: AsyncSession, bronze_dir: Path) -> SubPenLoadResult:
    bronze_dir = bronze_dir.resolve()
    sub_rows = _substitution_rows(bronze_dir)
    pk_rows = _penalty_kick_rows(bronze_dir)

    sub_count = await _upsert_batches(
        session,
        WcSubstitution.__table__,
        sub_rows,
        ["id"],
        [
            "tournament_id",
            "match_id",
            "team_id",
            "player_id",
            "shirt_number",
            "minute_regulation",
            "minute_stoppage",
            "match_period",
            "going_off",
            "coming_on",
        ],
    )
    pk_count = await _upsert_batches(
        session,
        WcPenaltyKick.__table__,
        pk_rows,
        ["id"],
        [
            "tournament_id",
            "match_id",
            "team_id",
            "player_id",
            "shirt_number",
            "converted",
        ],
    )
    return SubPenLoadResult(substitutions=sub_count, penalty_kicks=pk_count)
