"""Load World Cup standings, awards, and referee tables from Bronze CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.loaders.events import _upsert_batches
from app.etl.worldcup.transforms import clean_url, parse_bool, parse_int
from app.models.worldcup.officials import WcReferee, WcRefereeAppearance
from app.models.worldcup.standings import (
    WcAward,
    WcAwardWinner,
    WcGroupStanding,
    WcQualifiedTeam,
)


@dataclass(frozen=True)
class StandingsRefsLoadResult:
    awards: int
    award_winners: int
    qualified_teams: int
    group_standings: int
    referees: int
    referee_appearances: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _nullable_text(value: str) -> str | None:
    text = str(value).strip()
    if not text or text.lower() == "not applicable":
        return None
    return text


def _award_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "awards.csv")
    return [
        {
            "id": row["award_id"],
            "name": row["award_name"],
            "description": _nullable_text(row["award_description"]),
            "year_introduced": parse_int(row["year_introduced"]),
        }
        for _, row in df.iterrows()
    ]


def _award_winner_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "award_winners.csv")
    return [
        {
            "tournament_id": row["tournament_id"],
            "award_id": row["award_id"],
            "player_id": row["player_id"],
            "team_id": row["team_id"],
            "shared": parse_bool(row["shared"]),
        }
        for _, row in df.iterrows()
    ]


def _qualified_team_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "qualified_teams.csv")
    return [
        {
            "tournament_id": row["tournament_id"],
            "team_id": row["team_id"],
            "count_matches": int(row["count_matches"]),
            "performance": _nullable_text(row["performance"]),
        }
        for _, row in df.iterrows()
    ]


def _group_standing_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "group_standings.csv")
    return [
        {
            "tournament_id": row["tournament_id"],
            "stage_number": int(row["stage_number"]),
            "group_name": row["group_name"],
            "team_id": row["team_id"],
            "stage_name": row["stage_name"],
            "position": int(row["position"]),
            "played": int(row["played"]),
            "wins": int(row["wins"]),
            "draws": int(row["draws"]),
            "losses": int(row["losses"]),
            "goals_for": int(row["goals_for"]),
            "goals_against": int(row["goals_against"]),
            "goal_difference": int(row["goal_difference"]),
            "points": int(row["points"]),
            "advanced": parse_bool(row["advanced"]),
        }
        for _, row in df.iterrows()
    ]


def _referee_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "referees.csv")
    return [
        {
            "id": row["referee_id"],
            "family_name": row["family_name"],
            "given_name": row["given_name"],
            "female": parse_bool(row["female"]),
            "country_name": _nullable_text(row["country_name"]),
            "confederation_id": row["confederation_id"],
            "wikipedia_link": clean_url(row["referee_wikipedia_link"]),
        }
        for _, row in df.iterrows()
    ]


def _referee_appearance_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "referee_appearances.csv")
    return [
        {
            "match_id": row["match_id"],
            "tournament_id": row["tournament_id"],
            "referee_id": row["referee_id"],
        }
        for _, row in df.iterrows()
    ]


async def load_standings_refs(
    session: AsyncSession,
    bronze_dir: Path,
) -> StandingsRefsLoadResult:
    bronze_dir = bronze_dir.resolve()

    awards = await _upsert_batches(
        session,
        WcAward.__table__,
        _award_rows(bronze_dir),
        ["id"],
        ["name", "description", "year_introduced"],
    )
    referees = await _upsert_batches(
        session,
        WcReferee.__table__,
        _referee_rows(bronze_dir),
        ["id"],
        ["family_name", "given_name", "female", "country_name", "confederation_id", "wikipedia_link"],
    )
    award_winners = await _upsert_batches(
        session,
        WcAwardWinner.__table__,
        _award_winner_rows(bronze_dir),
        ["tournament_id", "award_id", "player_id"],
        ["team_id", "shared"],
    )
    qualified_teams = await _upsert_batches(
        session,
        WcQualifiedTeam.__table__,
        _qualified_team_rows(bronze_dir),
        ["tournament_id", "team_id"],
        ["count_matches", "performance"],
    )
    group_standings = await _upsert_batches(
        session,
        WcGroupStanding.__table__,
        _group_standing_rows(bronze_dir),
        ["tournament_id", "stage_number", "group_name", "team_id"],
        [
            "stage_name",
            "position",
            "played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
            "advanced",
        ],
    )
    referee_appearances = await _upsert_batches(
        session,
        WcRefereeAppearance.__table__,
        _referee_appearance_rows(bronze_dir),
        ["match_id"],
        ["tournament_id", "referee_id"],
    )

    return StandingsRefsLoadResult(
        awards=awards,
        award_winners=award_winners,
        qualified_teams=qualified_teams,
        group_standings=group_standings,
        referees=referees,
        referee_appearances=referee_appearances,
    )
