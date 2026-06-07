"""Silver-layer validation for World Cup PostgreSQL tables."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EXPECTED_COUNTS: dict[str, int] = {
    "wc_confederations": 6,
    "wc_teams": 88,
    "wc_tournaments": 30,
    "wc_stadiums": 240,
    "wc_players": 10401,
    "wc_player_tournament_years": 13843,
    "wc_matches": 1248,
    "wc_team_match_stats": 2496,
    "wc_goals": 3637,
    "wc_squads": 13843,
    "wc_bookings": 3178,
    "wc_substitutions": 10222,
    "wc_penalty_kicks": 396,
    "wc_player_appearances": 27432,
}

TOURNAMENT_GOLDEN: dict[str, dict[str, int | str]] = {
    "WC-2022": {
        "wc_matches": 64,
        "wc_goals": 172,
        "wc_squads": 831,
        "wc_player_appearances": 1995,
        "final_match_id": "M-2022-64",
        "final_home_score": 3,
        "final_away_score": 3,
    },
}

FK_CHECKS: list[tuple[str, str]] = [
    ("wc_teams.confederation_id", "wc_teams", "confederation_id", "wc_confederations", "id"),
    ("wc_matches.tournament_id", "wc_matches", "tournament_id", "wc_tournaments", "id"),
    ("wc_matches.stadium_id", "wc_matches", "stadium_id", "wc_stadiums", "id"),
    ("wc_matches.home_team_id", "wc_matches", "home_team_id", "wc_teams", "id"),
    ("wc_matches.away_team_id", "wc_matches", "away_team_id", "wc_teams", "id"),
    ("wc_goals.match_id", "wc_goals", "match_id", "wc_matches", "id"),
    ("wc_goals.player_id", "wc_goals", "player_id", "wc_players", "id"),
    ("wc_squads.player_id", "wc_squads", "player_id", "wc_players", "id"),
    ("wc_bookings.match_id", "wc_bookings", "match_id", "wc_matches", "id"),
    ("wc_substitutions.match_id", "wc_substitutions", "match_id", "wc_matches", "id"),
    ("wc_substitutions.player_id", "wc_substitutions", "player_id", "wc_players", "id"),
    ("wc_penalty_kicks.match_id", "wc_penalty_kicks", "match_id", "wc_matches", "id"),
    ("wc_penalty_kicks.player_id", "wc_penalty_kicks", "player_id", "wc_players", "id"),
    (
        "wc_player_appearances.match_id",
        "wc_player_appearances",
        "match_id",
        "wc_matches",
        "id",
    ),
    (
        "wc_player_appearances.player_id",
        "wc_player_appearances",
        "player_id",
        "wc_players",
        "id",
    ),
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    message: str


async def _scalar(session: AsyncSession, sql: str, params: dict | None = None) -> int:
    result = await session.execute(text(sql), params or {})
    value = result.scalar()
    return int(value or 0)


async def _check_table_counts(
    session: AsyncSession, tournament_id: str | None
) -> list[CheckResult]:
    results: list[CheckResult] = []
    if tournament_id:
        spec = TOURNAMENT_GOLDEN.get(tournament_id)
        if spec is None:
            return [
                CheckResult(
                    name=f"golden.{tournament_id}",
                    passed=False,
                    message=f"no golden spec for tournament {tournament_id}",
                )
            ]
        tournament_tables = (
            "wc_matches",
            "wc_goals",
            "wc_squads",
            "wc_player_appearances",
        )
        for table in tournament_tables:
            if table not in spec:
                continue
            expected = int(spec[table])
            actual = await _scalar(
                session,
                f"SELECT COUNT(*) FROM {table} WHERE tournament_id = :tid",
                {"tid": tournament_id},
            )
            results.append(
                CheckResult(
                    name=f"count.{table}.{tournament_id}",
                    passed=actual == expected,
                    message=f"expected {expected}, got {actual}",
                )
            )
        final_id = str(spec["final_match_id"])
        row = await session.execute(
            text(
                "SELECT home_score, away_score FROM wc_matches "
                "WHERE id = :mid AND tournament_id = :tid"
            ),
            {"mid": final_id, "tid": tournament_id},
        )
        final = row.one_or_none()
        if final is None:
            results.append(
                CheckResult(
                    name=f"golden.final.{tournament_id}",
                    passed=False,
                    message=f"final match {final_id} not found",
                )
            )
        else:
            home_score, away_score = final
            expected_home = int(spec["final_home_score"])
            expected_away = int(spec["final_away_score"])
            passed = home_score == expected_home and away_score == expected_away
            results.append(
                CheckResult(
                    name=f"golden.final_score.{tournament_id}",
                    passed=passed,
                    message=(
                        f"{final_id}: expected {expected_home}-{expected_away}, "
                        f"got {home_score}-{away_score}"
                    ),
                )
            )
        return results

    for table, expected in EXPECTED_COUNTS.items():
        actual = await _scalar(session, f"SELECT COUNT(*) FROM {table}")
        results.append(
            CheckResult(
                name=f"count.{table}",
                passed=actual == expected,
                message=f"expected {expected}, got {actual}",
            )
        )
    return results


async def _check_fk_orphans(session: AsyncSession) -> list[CheckResult]:
    results: list[CheckResult] = []
    for label, child_table, child_col, parent_table, parent_col in FK_CHECKS:
        orphans = await _scalar(
            session,
            f"""
            SELECT COUNT(*) FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
            WHERE p.{parent_col} IS NULL
            """,
        )
        results.append(
            CheckResult(
                name=f"fk.{label}",
                passed=orphans == 0,
                message=f"{orphans} orphan rows",
            )
        )
    return results


async def _check_business_rules(session: AsyncSession) -> list[CheckResult]:
    results: list[CheckResult] = []

    bad_team_rows = await _scalar(
        session,
        """
        SELECT COUNT(*) FROM (
            SELECT match_id FROM wc_team_match_stats
            GROUP BY match_id HAVING COUNT(*) != 2
        ) bad
        """,
    )
    results.append(
        CheckResult(
            name="business.team_match_stats_two_rows",
            passed=bad_team_rows == 0,
            message=f"{bad_team_rows} matches without exactly 2 team rows",
        )
    )

    player_year_mismatch = await _scalar(
        session,
        """
        SELECT COUNT(*) FROM wc_players p
        LEFT JOIN (
            SELECT player_id, COUNT(*) AS year_count
            FROM wc_player_tournament_years
            GROUP BY player_id
        ) y ON p.id = y.player_id
        WHERE p.count_tournaments != COALESCE(y.year_count, 0)
        """,
    )
    results.append(
        CheckResult(
            name="business.player_tournament_year_count",
            passed=player_year_mismatch == 0,
            message=f"{player_year_mismatch} players with year count mismatch",
        )
    )

    bad_own_goals = await _scalar(
        session,
        """
        SELECT COUNT(*) FROM wc_goals
        WHERE own_goal = true AND team_id = player_team_id
        """,
    )
    results.append(
        CheckResult(
            name="business.own_goal_team_mismatch",
            passed=bad_own_goals == 0,
            message=f"{bad_own_goals} own goals with same team_id and player_team_id",
        )
    )

    bad_replays = await _scalar(
        session,
        """
        SELECT COUNT(*) FROM wc_matches
        WHERE is_replay = true AND replay_of_match_id IS NULL
        """,
    )
    results.append(
        CheckResult(
            name="business.replay_linkage",
            passed=bad_replays == 0,
            message=f"{bad_replays} replay matches missing replay_of_match_id",
        )
    )

    return results


async def run_validation(
    session: AsyncSession,
    tournament_id: str | None = None,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(await _check_table_counts(session, tournament_id))
    if tournament_id is None:
        results.extend(await _check_fk_orphans(session))
        results.extend(await _check_business_rules(session))
    return results


def format_report(results: list[CheckResult]) -> str:
    lines = ["World Cup Silver validation", ""]
    failed = 0
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        if not item.passed:
            failed += 1
        lines.append(f"[{status}] {item.name}: {item.message}")
    lines.append("")
    lines.append(f"Summary: {len(results) - failed}/{len(results)} passed")
    if failed:
        lines.append(f"FAILED: {failed} check(s)")
    return "\n".join(lines)
