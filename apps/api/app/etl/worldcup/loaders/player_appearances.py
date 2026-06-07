"""Load World Cup player appearances from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.loaders.events import _upsert_batches
from app.etl.worldcup.transforms import parse_bool, parse_shirt_number
from app.models.worldcup.appearances import WcPlayerAppearance


@dataclass(frozen=True)
class PlayerAppearanceLoadResult:
    player_appearances: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _nullable_text(value: str) -> str | None:
    text = str(value).strip()
    if not text or text.lower() == "not applicable":
        return None
    return text


def _player_appearance_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "player_appearances.csv")
    return [
        {
            "match_id": row["match_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "tournament_id": row["tournament_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "position_name": _nullable_text(row["position_name"]),
            "position_code": _nullable_text(row["position_code"]),
            "starter": parse_bool(row["starter"]),
            "substitute": parse_bool(row["substitute"]),
        }
        for _, row in df.iterrows()
    ]


async def load_player_appearances(
    session: AsyncSession,
    bronze_dir: Path,
) -> PlayerAppearanceLoadResult:
    bronze_dir = bronze_dir.resolve()
    rows = _player_appearance_rows(bronze_dir)
    count = await _upsert_batches(
        session,
        WcPlayerAppearance.__table__,
        rows,
        ["match_id", "team_id", "player_id"],
        [
            "tournament_id",
            "shirt_number",
            "position_name",
            "position_code",
            "starter",
            "substitute",
        ],
    )
    return PlayerAppearanceLoadResult(player_appearances=count)
