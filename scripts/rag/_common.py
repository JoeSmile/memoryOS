"""Shared helpers for EP04-03 retrieval sandbox scripts (offline learning)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
GOLD_DIR = REPO_ROOT / "data" / "gold" / "worldcup" / "fact_cards"
EVAL_QUERIES_PATH = Path(__file__).resolve().parent / "eval_queries.yaml"

# Import after sys.path is set by callers.
EMBEDDING_DIMENSIONS = 1024


@dataclass(frozen=True)
class FactCard:
    id: str
    collection: str
    entity_type: str | None
    text: str


@dataclass(frozen=True)
class RankedHit:
    doc_id: str
    collection: str
    score: float
    text_preview: str


def tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower()) if len(t) > 1}


def load_fact_cards(
    *,
    stems: list[str] | None = None,
    limit_per_file: int | None = 200,
) -> list[FactCard]:
    """Load Gold JSONL into memory for offline experiments."""
    stems = stems or ["matches", "player_careers", "players"]
    cards: list[FactCard] = []
    for stem in stems:
        path = GOLD_DIR / f"{stem}.jsonl"
        if not path.is_file():
            continue
        collection = f"worldcup-{stem}"
        with path.open(encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if limit_per_file is not None and i >= limit_per_file:
                    break
                row = json.loads(line)
                cards.append(
                    FactCard(
                        id=row["id"],
                        collection=collection,
                        entity_type=row.get("entity_type"),
                        text=row["text"],
                    )
                )
    return cards


def mock_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    from app.services.embedding_service import _mock_embedding

    return _mock_embedding(text, dimensions)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def vector_rank(query: str, cards: list[FactCard], top_k: int = 10) -> list[RankedHit]:
    qv = mock_embedding(query)
    scored: list[tuple[FactCard, float]] = []
    for card in cards:
        score = cosine_similarity(qv, mock_embedding(card.text))
        scored.append((card, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [_to_hit(card, score) for card, score in scored[:top_k]]


def keyword_rank(query: str, cards: list[FactCard], top_k: int = 10) -> list[RankedHit]:
    """Cheap BM25 stand-in: token overlap count (install rank_bm25 for real BM25)."""
    q_tokens = tokenize(query)
    if not q_tokens:
        return []

    scored: list[tuple[FactCard, float]] = []
    for card in cards:
        doc_tokens = tokenize(card.text)
        score = float(len(q_tokens & doc_tokens))
        if score > 0:
            scored.append((card, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [_to_hit(card, score) for card, score in scored[:top_k]]


def reciprocal_rank_fusion(
    ranked_lists: list[list[RankedHit]],
    *,
    k: int = 60,
    top_k: int = 10,
) -> list[RankedHit]:
    """RRF: score(d) = sum 1 / (k + rank_i(d)). Interview staple."""
    scores: dict[str, float] = {}
    meta: dict[str, RankedHit] = {}
    for ranked in ranked_lists:
        for rank, hit in enumerate(ranked, start=1):
            scores[hit.doc_id] = scores.get(hit.doc_id, 0.0) + 1.0 / (k + rank)
            meta.setdefault(hit.doc_id, hit)
    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    return [
        RankedHit(
            doc_id=doc_id,
            collection=meta[doc_id].collection,
            score=score,
            text_preview=meta[doc_id].text_preview,
        )
        for doc_id, score in fused
    ]


def precision_at_k(hits: list[RankedHit], expected_id: str, k: int = 5) -> float:
    top = hits[:k]
    return 1.0 if any(h.doc_id == expected_id for h in top) else 0.0


def print_hits(title: str, hits: list[RankedHit], *, max_rows: int = 5) -> None:
    print(f"\n=== {title} ===")
    if not hits:
        print("  (no hits)")
        return
    for i, hit in enumerate(hits[:max_rows], start=1):
        print(
            f"  {i}. score={hit.score:.4f} id={hit.doc_id} "
            f"collection={hit.collection}"
        )
        print(f"     {hit.text_preview[:120]}...")


def _to_hit(card: FactCard, score: float) -> RankedHit:
    preview = card.text.replace("\n", " ")
    return RankedHit(
        doc_id=card.id,
        collection=card.collection,
        score=score,
        text_preview=preview,
    )


def load_eval_queries(path: Path = EVAL_QUERIES_PATH) -> list[dict[str, Any]]:
    """Load YAML eval set when PyYAML is available; else return built-in samples."""
    if path.is_file():
        try:
            import yaml

            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return list(data.get("queries", []))
        except ImportError:
            print("note: pip install pyyaml to load eval_queries.yaml; using built-ins")

    return [
        {
            "query": "Messi World Cup 2022 final",
            "expected_id": None,
            "note": "fill expected_id after manual check",
        },
        {
            "query": "1930 France Mexico 4-1",
            "expected_id": "match:M-1930-01",
            "note": "exact score line in matches",
        },
        {
            "query": "Lionel Messi career World Cup",
            "expected_id": None,
            "collection": "worldcup-player-careers",
        },
    ]
