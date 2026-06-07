#!/usr/bin/env python3
"""Run a tiny P@5 baseline over eval queries (EP04-03 Story 4.01 skeleton)."""

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
    parser.add_argument("--limit", type=int, default=500, help="Max lines per gold jsonl")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--mode",
        choices=("vector", "hybrid"),
        default="vector",
        help="vector=mock embed only; hybrid=RRF(vector, keyword)",
    )
    args = parser.parse_args()

    cards = common.load_fact_cards(limit_per_file=args.limit)
    queries = common.load_eval_queries()

    scored = 0
    total = 0
    print(f"eval queries: {len(queries)}  corpus: {len(cards)} cards  mode={args.mode}\n")

    for item in queries:
        q = item["query"]
        expected = item.get("expected_id")
        if not expected:
            print(f"  skip (no expected_id): {q!r}")
            continue
        if args.mode == "hybrid":
            hits = common.reciprocal_rank_fusion(
                [
                    common.vector_rank(q, cards, top_k=max(args.k, 10)),
                    common.keyword_rank(q, cards, top_k=max(args.k, 10)),
                ],
                top_k=args.k,
            )
        else:
            hits = common.vector_rank(q, cards, top_k=args.k)
        p = common.precision_at_k(hits, expected, k=args.k)
        scored += p
        total += 1
        mark = "OK" if p else "MISS"
        print(f"  [{mark}] P@{args.k}={p:.0f}  q={q!r}  want={expected}")

    if total:
        print(f"\nmean P@{args.k} over {total} labeled queries: {scored / total:.2f}")
        if args.mode == "vector":
            print(
                "tip: mock embed has no real semantics — rerun with --mode hybrid "
                "to see keyword+RRF lift on exact-match queries."
            )
    else:
        print("\nAdd expected_id entries to scripts/rag/eval_queries.yaml to score baseline.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
