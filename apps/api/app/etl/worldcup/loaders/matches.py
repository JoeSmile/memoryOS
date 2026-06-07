"""Load World Cup matches from Bronze CSV."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.worldcup.transforms import parse_bool, parse_date, parse_int
from app.models.worldcup.matches import WcMatch, WcTeamMatchStat

BATCH_SIZE = 2000


@dataclass(frozen=True)
class MatchLoadResult:
    matches: int
    team_match_stats: int


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _nullable_text(value: str) -> str | None:
    text = str(value).strip()
    return text or None


def _link_replay_of(match_rows: list[dict]) -> None:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in match_rows:
        grouped[(row["tournament_id"], row["name"])].append(row)

    for row in match_rows:
        if not row["is_replay"]:
            continue
        partners = grouped[(row["tournament_id"], row["name"])]
        original = next(
            (item for item in partners if item["is_replayed"] and item["id"] != row["id"]),
            None,
        )
        if original is None:
            msg = f"replay match {row['id']} has no replayed partner"
            raise ValueError(msg)
        row["replay_of_match_id"] = original["id"]


def _match_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "matches.csv")
    rows: list[dict] = []
    for _, row in df.iterrows():
        home_pen = parse_int(row["home_team_score_penalties"])
        away_pen = parse_int(row["away_team_score_penalties"])
        rows.append(
            {
                "id": row["match_id"],
                "tournament_id": row["tournament_id"],
                "name": row["match_name"],
                "stage_name": row["stage_name"],
                "group_name": _nullable_text(row["group_name"]),
                "group_stage": parse_bool(row["group_stage"]),
                "knockout_stage": parse_bool(row["knockout_stage"]),
                "is_replayed": parse_bool(row["replayed"]),
                "is_replay": parse_bool(row["replay"]),
                "replay_of_match_id": None,
                "match_date": parse_date(row["match_date"]),
                "match_time": _nullable_text(row["match_time"]),
                "stadium_id": row["stadium_id"],
                "home_team_id": row["home_team_id"],
                "away_team_id": row["away_team_id"],
                "home_score": int(row["home_team_score"]),
                "away_score": int(row["away_team_score"]),
                "extra_time": parse_bool(row["extra_time"]),
                "penalty_shootout": parse_bool(row["penalty_shootout"]),
                "home_penalty_score": home_pen,
                "away_penalty_score": away_pen,
            }
        )
    _link_replay_of(rows)
    return rows


def _team_stat_rows(bronze_dir: Path) -> list[dict]:
    df = _read_csv(bronze_dir / "team_appearances.csv")
    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "match_id": row["match_id"],
                "team_id": row["team_id"],
                "opponent_id": row["opponent_id"],
                "is_home": parse_bool(row["home_team"]),
                "goals_for": int(row["goals_for"]),
                "goals_against": int(row["goals_against"]),
                "goal_differential": int(row["goal_differential"]),
                "extra_time": parse_bool(row["extra_time"]),
                "penalty_shootout": parse_bool(row["penalty_shootout"]),
                "penalties_for": parse_int(row["penalties_for"]),
                "penalties_against": parse_int(row["penalties_against"]),
                "won": parse_bool(row["win"]),
                "lost": parse_bool(row["lose"]),
                "drew": parse_bool(row["draw"]),
            }
        )
    return rows


def _validate_team_stats(match_rows: list[dict], stat_rows: list[dict]) -> None:
    matches_by_id = {row["id"]: row for row in match_rows}
    by_match: dict[str, list[dict]] = defaultdict(list)
    for stat in stat_rows:
        by_match[stat["match_id"]].append(stat)

    for match_id, stats in by_match.items():
        if len(stats) != 2:
            raise ValueError(f"match {match_id}: expected 2 team rows, got {len(stats)}")
        match = matches_by_id[match_id]
        for stat in stats:
            if stat["team_id"] == match["home_team_id"]:
                expected_for, expected_against = match["home_score"], match["away_score"]
            elif stat["team_id"] == match["away_team_id"]:
                expected_for, expected_against = match["away_score"], match["home_score"]
            else:
                raise ValueError(
                    f"match {match_id}: team {stat['team_id']} not in home/away"
                )
            if stat["goals_for"] != expected_for or stat["goals_against"] != expected_against:
                raise ValueError(
                    f"match {match_id} team {stat['team_id']}: "
                    f"score {stat['goals_for']}-{stat['goals_against']} != "
                    f"expected {expected_for}-{expected_against}"
                )


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


async def load_matches(session: AsyncSession, bronze_dir: Path) -> MatchLoadResult:
    bronze_dir = bronze_dir.resolve()
    match_rows = _match_rows(bronze_dir)
    stat_rows = _team_stat_rows(bronze_dir)
    _validate_team_stats(match_rows, stat_rows)

    match_count = await _upsert_batches(
        session,
        WcMatch.__table__,
        match_rows,
        ["id"],
        [
            "tournament_id",
            "name",
            "stage_name",
            "group_name",
            "group_stage",
            "knockout_stage",
            "is_replayed",
            "is_replay",
            "replay_of_match_id",
            "match_date",
            "match_time",
            "stadium_id",
            "home_team_id",
            "away_team_id",
            "home_score",
            "away_score",
            "extra_time",
            "penalty_shootout",
            "home_penalty_score",
            "away_penalty_score",
        ],
    )
    stat_count = await _upsert_batches(
        session,
        WcTeamMatchStat.__table__,
        stat_rows,
        ["match_id", "team_id"],
        [
            "opponent_id",
            "is_home",
            "goals_for",
            "goals_against",
            "goal_differential",
            "extra_time",
            "penalty_shootout",
            "penalties_for",
            "penalties_against",
            "won",
            "lost",
            "drew",
        ],
    )
    return MatchLoadResult(matches=match_count, team_match_stats=stat_count)
