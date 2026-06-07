#!/usr/bin/env python3
"""Validate World Cup Silver PostgreSQL tables."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_DIR = REPO_ROOT / "apps" / "api"

sys.path.insert(0, str(API_DIR))


async def _run(tournament_id: str | None) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.validate import format_report, run_validation

    async with AsyncSessionLocal() as session:
        results = await run_validation(session, tournament_id=tournament_id)

    print(format_report(results))
    return 0 if all(item.passed for item in results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate World Cup Silver tables")
    parser.add_argument(
        "--tournament",
        help="Run golden-set checks for a tournament (e.g. WC-2022)",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.tournament))


if __name__ == "__main__":
    raise SystemExit(main())
