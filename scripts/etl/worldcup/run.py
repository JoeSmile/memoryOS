#!/usr/bin/env python3
"""World Cup ETL CLI — loads Bronze CSV into Silver PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_DIR = REPO_ROOT / "apps" / "api"
DEFAULT_BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"

sys.path.insert(0, str(API_DIR))


async def _run_standings(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.standings_refs import load_standings_refs

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_standings_refs(session, bronze_dir)

    print(
        "loaded standings/refs:",
        f"awards={result.awards}",
        f"award_winners={result.award_winners}",
        f"qualified_teams={result.qualified_teams}",
        f"group_standings={result.group_standings}",
        f"referees={result.referees}",
        f"referee_appearances={result.referee_appearances}",
    )
    return 0


async def _run_appearances(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.player_appearances import load_player_appearances

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_player_appearances(session, bronze_dir)

    print(f"loaded player_appearances: {result.player_appearances}")
    return 0


async def _run_subpen(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.sub_pen import load_sub_pen

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_sub_pen(session, bronze_dir)

    print(
        "loaded sub/pen:",
        f"substitutions={result.substitutions}",
        f"penalty_kicks={result.penalty_kicks}",
    )
    return 0


async def _run_events(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.events import load_events

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_events(session, bronze_dir)

    print(
        "loaded events:",
        f"goals={result.goals}",
        f"squads={result.squads}",
        f"bookings={result.bookings}",
    )
    return 0


async def _run_matches(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.matches import load_matches

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_matches(session, bronze_dir)

    print(
        "loaded matches:",
        f"matches={result.matches}",
        f"team_match_stats={result.team_match_stats}",
    )
    return 0


async def _run_players(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.players import load_players

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_players(session, bronze_dir)

    print(
        "loaded players:",
        f"players={result.players}",
        f"tournament_years={result.tournament_years}",
    )
    return 0


async def _run_dimensions(bronze_dir: Path) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.loaders.dimensions import load_dimensions

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await load_dimensions(session, bronze_dir)

    print(
        "loaded dimensions:",
        f"confederations={result.confederations}",
        f"teams={result.teams}",
        f"tournaments={result.tournaments}",
        f"stadiums={result.stadiums}",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="World Cup Bronze → Silver ETL")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("dimensions", "Load confederations, teams, tournaments, stadiums"),
        ("players", "Load players and tournament year bridge rows"),
        ("matches", "Load matches and team appearance stats"),
        ("events", "Load goals, squads, and bookings"),
        ("subpen", "Load substitutions and penalty kicks (P2)"),
        ("appearances", "Load player match appearances (P2)"),
        ("standings", "Load awards, standings, qualified teams, referees (P2)"),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument(
            "bronze_dir",
            nargs="?",
            default=str(DEFAULT_BRONZE_DIR),
            help=f"Bronze CSV directory (default: {DEFAULT_BRONZE_DIR})",
        )

    args = parser.parse_args(argv)
    bronze_dir = Path(args.bronze_dir)

    if not bronze_dir.is_dir():
        print(f"error: bronze directory not found: {bronze_dir}", file=sys.stderr)
        return 1

    if args.command == "dimensions":
        return asyncio.run(_run_dimensions(bronze_dir))
    if args.command == "players":
        return asyncio.run(_run_players(bronze_dir))
    if args.command == "matches":
        return asyncio.run(_run_matches(bronze_dir))
    if args.command == "events":
        return asyncio.run(_run_events(bronze_dir))
    if args.command == "subpen":
        return asyncio.run(_run_subpen(bronze_dir))
    if args.command == "appearances":
        return asyncio.run(_run_appearances(bronze_dir))
    if args.command == "standings":
        return asyncio.run(_run_standings(bronze_dir))

    print(f"error: unknown command {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
