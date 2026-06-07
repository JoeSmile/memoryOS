"""Load World Cup players from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.transforms import (
    clean_url,
    parse_bool,
    parse_optional_date,
    parse_int,
    parse_positions,
    player_display_name,
    split_tournament_years,
)
from app.models.worldcup import WcPlayer, WcPlayerTournamentYear

BATCH_SIZE = 2000


@dataclass(frozen=True)
class PlayerLoadResult:
    players: int
    tournament_years: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _player_rows(bronze_dir: Path) -> tuple[list[dict], list[dict]]:
    df = _read_csv(bronze_dir / "players.csv")
    players: list[dict] = []
    years: list[dict] = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        year_list = split_tournament_years(row_dict["list_tournaments"])
        count = parse_int(row_dict["count_tournaments"]) or 0
        if count != len(year_list):
            msg = (
                f"player {row_dict['player_id']}: count_tournaments={count} "
                f"!= years={len(year_list)}"
            )
            raise ValueError(msg)

        positions, primary = parse_positions(row_dict)
        players.append(
            {
                "id": row_dict["player_id"],
                "family_name": row_dict["family_name"],
                "given_name": row_dict["given_name"],
                "display_name": player_display_name(
                    row_dict["given_name"],
                    row_dict["family_name"],
                ),
                "birth_date": parse_optional_date(row_dict["birth_date"]),
                "female": parse_bool(row_dict["female"]),
                "positions": positions,
                "primary_position": primary,
                "count_tournaments": count,
                "wikipedia_link": clean_url(row_dict["player_wikipedia_link"]),
            }
        )
        for year in year_list:
            years.append({"player_id": row_dict["player_id"], "year": year})

    return players, years


async def _upsert_batches(
    session: AsyncSession,
    table,
    rows: list[dict],
    index_elements: list[str],
    update_columns: list[str],
) -> int:
    if not rows:
        return 0
    total = 0
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        stmt = insert(table).values(batch)
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_={column: getattr(excluded, column) for column in update_columns},
        )
        await session.execute(stmt)
        total += len(batch)
    return total


async def load_players(session: AsyncSession, bronze_dir: Path) -> PlayerLoadResult:
    bronze_dir = bronze_dir.resolve()
    player_rows, year_rows = _player_rows(bronze_dir)

    player_count = await _upsert_batches(
        session,
        WcPlayer.__table__,
        player_rows,
        ["id"],
        [
            "family_name",
            "given_name",
            "display_name",
            "birth_date",
            "female",
            "positions",
            "primary_position",
            "count_tournaments",
            "wikipedia_link",
        ],
    )

    await session.execute(delete(WcPlayerTournamentYear))
    year_count = 0
    if year_rows:
        for start in range(0, len(year_rows), BATCH_SIZE):
            batch = year_rows[start : start + BATCH_SIZE]
            await session.execute(insert(WcPlayerTournamentYear.__table__).values(batch))
            year_count += len(batch)

    return PlayerLoadResult(players=player_count, tournament_years=year_count)
