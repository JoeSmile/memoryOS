#!/usr/bin/env python3
"""Export World Cup Gold fact cards from Silver PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_DIR = REPO_ROOT / "apps" / "api"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "gold" / "worldcup" / "fact_cards"

sys.path.insert(0, str(API_DIR))


async def _run(output_dir: Path, tournament_id: str | None) -> int:
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.fact_cards import export_fact_cards

    async with AsyncSessionLocal() as session:
        counts = await export_fact_cards(session, output_dir, tournament_id)

    print("exported fact cards:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    print(f"output: {output_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export World Cup Gold fact cards")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--tournament",
        help="Limit export to one tournament (e.g. WC-2022)",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(Path(args.output_dir), args.tournament))


if __name__ == "__main__":
    raise SystemExit(main())
