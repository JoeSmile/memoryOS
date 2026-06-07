#!/usr/bin/env python3
"""Demonstrate RRF fusion across multiple retrieval lists (EP04-03 Story 4.05)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = RAG_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(RAG_DIR))

import _common as common


def _paraphrase_queries(query: str) -> list[str]:
    """Stub multi-query expansion — replace with LLM rewrite in production."""
    variants = [query]
    if "Messi" in query:
        variants.append(query.replace("Messi", "Lionel Messi"))
    if "World Cup" not in query and "world cup" not in query.lower():
        variants.append(f"{query} FIFA World Cup")
    return list(dict.fromkeys(variants))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()

    cards = common.load_fact_cards(limit_per_file=args.limit)
    queries = _paraphrase_queries(args.query)
    print(f"multi-query variants: {queries}")

    ranked_lists = [common.vector_rank(q, cards, top_k=10) for q in queries]
    for i, q in enumerate(queries):
        common.print_hits(f"vector list #{i + 1}: {q!r}", ranked_lists[i], max_rows=3)

    fused = common.reciprocal_rank_fusion(ranked_lists, top_k=args.top_k)
    common.print_hits("RRF fused", fused, max_rows=args.top_k)

    print(
        "\nRRF formula: score(d) = sum_i 1/(k + rank_i(d)), default k=60. "
        "No score normalization across lists — robust when scales differ."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
