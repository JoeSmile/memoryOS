#!/usr/bin/env python3
"""Two-stage retrieve → rerank demo (EP04-03 Story 4.04 learning sandbox)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = RAG_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(RAG_DIR))

import _common as common


def stub_cross_encoder_rerank(
    query: str, candidates: list[common.RankedHit], top_k: int
) -> list[common.RankedHit]:
    """
    Placeholder reranker: token overlap on (query, chunk) — NOT a real cross-encoder.

    TODO (EP04-03): swap for Cohere rerank API or local CE model, e.g.:
      - sentence-transformers CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
      - scores = model.predict([(query, hit.text_preview) for hit in candidates])
    """
    q = common.tokenize(query)
    rescored: list[tuple[common.RankedHit, float]] = []
    for hit in candidates:
        overlap = len(q & common.tokenize(hit.text_preview))
        rescored.append((hit, float(overlap)))
    rescored.sort(key=lambda item: item[1], reverse=True)
    return [
        common.RankedHit(
            doc_id=hit.doc_id,
            collection=hit.collection,
            score=score,
            text_preview=hit.text_preview,
        )
        for hit, score in rescored[:top_k]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--recall-k", type=int, default=20, help="Stage-1 vector recall width")
    parser.add_argument("--top-k", type=int, default=5, help="Stage-2 rerank output")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    cards = common.load_fact_cards(limit_per_file=args.limit)
    stage1 = common.vector_rank(args.query, cards, top_k=args.recall_k)
    stage2 = stub_cross_encoder_rerank(args.query, stage1, top_k=args.top_k)

    common.print_hits(f"stage-1 vector recall (top {args.recall_k})", stage1, max_rows=5)
    common.print_hits(f"stage-2 stub rerank (top {args.top_k})", stage2, max_rows=args.top_k)

    print(
        "\nInterview tip: Bi-encoder (embedding) is fast but approximate; "
        "cross-encoder scores query+doc jointly — use recall wide, rerank narrow."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
