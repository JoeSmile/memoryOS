"""Load World Cup match events from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.transforms import parse_bool, parse_int, parse_shirt_number
from app.models.worldcup.events import WcBooking, WcGoal, WcSquad

BATCH_SIZE = 2000


@dataclass(frozen=True)
class EventLoadResult:
    goals: int
    squads: int
    bookings: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _nullable_text(value: str) -> str | None:
    text = str(value).strip()
    return text or None


def _goal_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "goals.csv")
    return [
        {
            "id": row["goal_id"],
            "tournament_id": row["tournament_id"],
            "match_id": row["match_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "player_team_id": row["player_team_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "minute_regulation": int(row["minute_regulation"]),
            "minute_stoppage": int(row["minute_stoppage"] or 0),
            "match_period": row["match_period"],
            "own_goal": parse_bool(row["own_goal"]),
            "penalty": parse_bool(row["penalty"]),
        }
        for _, row in df.iterrows()
    ]


def _squad_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "squads.csv")
    return [
        {
            "tournament_id": row["tournament_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "position_name": _nullable_text(row["position_name"]),
            "position_code": _nullable_text(row["position_code"]),
        }
        for _, row in df.iterrows()
    ]


def _booking_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "bookings.csv")
    return [
        {
            "id": row["booking_id"],
            "tournament_id": row["tournament_id"],
            "match_id": row["match_id"],
            "team_id": row["team_id"],
            "player_id": row["player_id"],
            "shirt_number": parse_shirt_number(row["shirt_number"]),
            "minute_regulation": int(row["minute_regulation"]),
            "minute_stoppage": int(row["minute_stoppage"] or 0),
            "match_period": row["match_period"],
            "yellow_card": parse_bool(row["yellow_card"]),
            "red_card": parse_bool(row["red_card"]),
            "second_yellow_card": parse_bool(row["second_yellow_card"]),
            "sending_off": parse_bool(row["sending_off"]),
        }
        for _, row in df.iterrows()
    ]


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


async def load_events(session: AsyncSession, bronze_dir: Path) -> EventLoadResult:
    bronze_dir = bronze_dir.resolve()
    goal_rows = _goal_rows(bronze_dir)
    squad_rows = _squad_rows(bronze_dir)
    booking_rows = _booking_rows(bronze_dir)

    goal_count = await _upsert_batches(
        session,
        WcGoal.__table__,
        goal_rows,
        ["id"],
        [
            "tournament_id",
            "match_id",
            "team_id",
            "player_id",
            "player_team_id",
            "shirt_number",
            "minute_regulation",
            "minute_stoppage",
            "match_period",
            "own_goal",
            "penalty",
        ],
    )
    squad_count = await _upsert_batches(
        session,
        WcSquad.__table__,
        squad_rows,
        ["tournament_id", "team_id", "player_id"],
        ["shirt_number", "position_name", "position_code"],
    )
    booking_count = await _upsert_batches(
        session,
        WcBooking.__table__,
        booking_rows,
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
            "yellow_card",
            "red_card",
            "second_yellow_card",
            "sending_off",
        ],
    )
    return EventLoadResult(
        goals=goal_count,
        squads=squad_count,
        bookings=booking_count,
    )
