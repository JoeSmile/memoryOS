#!/usr/bin/env python3
"""Compare vector-only vs keyword + vector RRF (EP04-03 Story 4.03 learning sandbox)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = RAG_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(RAG_DIR))

import _common as common


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--stems",
        default="matches,player_careers",
        help="Gold jsonl stems (comma-separated)",
    )
    parser.add_argument("--limit", type=int, default=300, help="Max lines per jsonl file")
    args = parser.parse_args()

    stems = [s.strip() for s in args.stems.split(",") if s.strip()]
    cards = common.load_fact_cards(stems=stems, limit_per_file=args.limit)
    print(f"loaded {len(cards)} fact cards from {stems}")

    vec_hits = common.vector_rank(args.query, cards, top_k=max(args.top_k, 10))
    kw_hits = common.keyword_rank(args.query, cards, top_k=max(args.top_k, 10))
    hybrid_hits = common.reciprocal_rank_fusion([vec_hits, kw_hits], top_k=args.top_k)

    common.print_hits("vector only (mock embed + cosine)", vec_hits, max_rows=args.top_k)
    common.print_hits("keyword only (token overlap stub)", kw_hits, max_rows=args.top_k)
    common.print_hits("hybrid (RRF of vector + keyword)", hybrid_hits, max_rows=args.top_k)

    print(
        "\nInterview tip: Hybrid helps when query has exact tokens (scores, names, dates) "
        "that dense vectors blur. Replace keyword_rank with Postgres FTS or rank_bm25 next."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
