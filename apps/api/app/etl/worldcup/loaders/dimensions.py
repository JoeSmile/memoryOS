"""Load World Cup dimension tables from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.transforms import (
    clean_url,
    parse_bool,
    parse_date,
    parse_int,
    tournament_slug,
)
from app.models.worldcup import WcConfederation, WcStadium, WcTeam, WcTournament


@dataclass(frozen=True)
class DimensionLoadResult:
    confederations: int
    teams: int
    tournaments: int
    stadiums: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


async def _upsert_rows(
    session: AsyncSession,
    table,
    rows: list[dict],
    index_elements: list[str],
    update_columns: list[str],
) -> int:
    if not rows:
        return 0
    stmt = insert(table).values(rows)
    excluded = stmt.excluded
    stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_={column: getattr(excluded, column) for column in update_columns},
    )
    await session.execute(stmt)
    return len(rows)


def _confederation_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "confederations.csv")
    return [
        {
            "id": row["confederation_id"],
            "name": row["confederation_name"],
            "code": row["confederation_code"],
            "wikipedia_link": clean_url(row["confederation_wikipedia_link"]),
        }
        for _, row in df.iterrows()
    ]


def _team_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "teams.csv")
    return [
        {
            "id": row["team_id"],
            "name": row["team_name"],
            "code": row["team_code"],
            "mens_team": parse_bool(row["mens_team"]),
            "womens_team": parse_bool(row["womens_team"]),
            "federation_name": row["federation_name"] or None,
            "region_name": row["region_name"] or None,
            "confederation_id": row["confederation_id"],
            "mens_team_wikipedia_link": clean_url(row["mens_team_wikipedia_link"]),
            "womens_team_wikipedia_link": clean_url(row["womens_team_wikipedia_link"]),
            "federation_wikipedia_link": clean_url(row["federation_wikipedia_link"]),
        }
        for _, row in df.iterrows()
    ]


def _tournament_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "tournaments.csv")
    bool_cols = [
        "group_stage",
        "second_group_stage",
        "final_round",
        "round_of_16",
        "quarter_finals",
        "semi_finals",
        "third_place_match",
        "final",
    ]
    rows: list[dict] = []
    for _, row in df.iterrows():
        entry = {
            "id": row["tournament_id"],
            "slug": tournament_slug(row["tournament_id"]),
            "name": row["tournament_name"],
            "year": int(row["year"]),
            "start_date": parse_date(row["start_date"]),
            "end_date": parse_date(row["end_date"]),
            "host_country": row["host_country"] or None,
            "winner": row["winner"] or None,
            "host_won": parse_bool(row["host_won"]),
            "count_teams": parse_int(row["count_teams"]),
        }
        for col in bool_cols:
            entry[col] = parse_bool(row[col])
        rows.append(entry)
    return rows


def _stadium_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "stadiums.csv")
    return [
        {
            "id": row["stadium_id"],
            "name": row["stadium_name"],
            "city_name": row["city_name"],
            "country_name": row["country_name"],
            "capacity": parse_int(row["stadium_capacity"]),
            "stadium_wikipedia_link": clean_url(row["stadium_wikipedia_link"]),
            "city_wikipedia_link": clean_url(row["city_wikipedia_link"]),
        }
        for _, row in df.iterrows()
    ]


async def load_dimensions(session: AsyncSession, bronze_dir: Path) -> DimensionLoadResult:
    bronze_dir = bronze_dir.resolve()
    conf_rows = _confederation_rows(bronze_dir)
    team_rows = _team_rows(bronze_dir)
    tournament_rows = _tournament_rows(bronze_dir)
    stadium_rows = _stadium_rows(bronze_dir)

    conf_count = await _upsert_rows(
        session,
        WcConfederation.__table__,
        conf_rows,
        ["id"],
        ["name", "code", "wikipedia_link"],
    )
    team_count = await _upsert_rows(
        session,
        WcTeam.__table__,
        team_rows,
        ["id"],
        [
            "name",
            "code",
            "mens_team",
            "womens_team",
            "federation_name",
            "region_name",
            "confederation_id",
            "mens_team_wikipedia_link",
            "womens_team_wikipedia_link",
            "federation_wikipedia_link",
        ],
    )
    tournament_count = await _upsert_rows(
        session,
        WcTournament.__table__,
        tournament_rows,
        ["id"],
        [
            "slug",
            "name",
            "year",
            "start_date",
            "end_date",
            "host_country",
            "winner",
            "host_won",
            "count_teams",
            "group_stage",
            "second_group_stage",
            "final_round",
            "round_of_16",
            "quarter_finals",
            "semi_finals",
            "third_place_match",
            "final",
        ],
    )
    stadium_count = await _upsert_rows(
        session,
        WcStadium.__table__,
        stadium_rows,
        ["id"],
        [
            "name",
            "city_name",
            "country_name",
            "capacity",
            "stadium_wikipedia_link",
            "city_wikipedia_link",
        ],
    )

    return DimensionLoadResult(
        confederations=conf_count,
        teams=team_count,
        tournaments=tournament_count,
        stadiums=stadium_count,
    )
