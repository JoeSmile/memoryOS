#!/usr/bin/env python3
"""Ingest World Cup Gold fact cards into pgvector (documents / document_chunks)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_DIR = REPO_ROOT / "apps" / "api"
DEFAULT_GOLD_DIR = REPO_ROOT / "data" / "gold" / "worldcup" / "fact_cards"

sys.path.insert(0, str(API_DIR))


async def _run(gold_dir: Path, collection_stems: list[str] | None) -> int:
    from app.core.database import AsyncSessionLocal
    from app.core.redis import ensure_redis
    from app.services.knowledge_ingest_service import (
        DEFAULT_COLLECTION_STEMS,
        KnowledgeIngestError,
        KnowledgeIngestInProgressError,
        KnowledgeIngestService,
    )

    redis = await ensure_redis()
    async with AsyncSessionLocal() as session:
        service = KnowledgeIngestService(session, gold_dir=gold_dir, redis=redis)
        try:
            summary = await service.ingest_worldcup_fact_cards(collection_stems)
        except KnowledgeIngestInProgressError as exc:
            print(f"ingest already in progress: stems={exc.stems}", file=sys.stderr)
            return 1
        except KnowledgeIngestError as exc:
            print(f"ingest failed: {exc}", file=sys.stderr)
            if exc.external_ids:
                print(f"  collection={exc.collection} ids={exc.external_ids}", file=sys.stderr)
            return 1

    stems = collection_stems or list(DEFAULT_COLLECTION_STEMS)
    print(f"ingested gold fact cards from {gold_dir}")
    print(f"collections: {', '.join(stems)}")
    for item in summary.collections:
        print(
            f"  {item.collection}: lines={item.lines_read} "
            f"created={item.documents_created} updated={item.documents_updated} "
            f"skipped={item.documents_skipped}"
        )
    print(f"total lines: {summary.total_lines}")
    return 0


def _parse_collections(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    stems = [part.strip() for part in raw.split(",") if part.strip()]
    if not stems:
        return None
    return stems


def main(argv: list[str] | None = None) -> int:
    from app.services.knowledge_ingest_service import DEFAULT_COLLECTION_STEMS

    parser = argparse.ArgumentParser(
        description="Ingest World Cup Gold JSONL into RAG documents/document_chunks",
    )
    parser.add_argument(
        "--gold-dir",
        default=str(DEFAULT_GOLD_DIR),
        help=f"Gold fact_cards directory (default: {DEFAULT_GOLD_DIR})",
    )
    parser.add_argument(
        "--collections",
        help=(
            "Comma-separated jsonl stems to ingest (default: all). "
            f"Allowed: {', '.join(DEFAULT_COLLECTION_STEMS)}"
        ),
    )
    args = parser.parse_args(argv)

    collection_stems = _parse_collections(args.collections)
    if collection_stems is not None:
        allowed = set(DEFAULT_COLLECTION_STEMS)
        unknown = [stem for stem in collection_stems if stem not in allowed]
        if unknown:
            parser.error(
                f"unknown collection stems: {unknown}. "
                f"Allowed: {', '.join(DEFAULT_COLLECTION_STEMS)}"
            )

    return asyncio.run(_run(Path(args.gold_dir), collection_stems))


if __name__ == "__main__":
    raise SystemExit(main())
