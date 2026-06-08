from app.services.knowledge_ingest_service import (
    can_skip_unchanged,
    content_hash,
    ingest_metadata,
)

_EMBED_DIM = 1024


def test_content_hash_stable():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("world")


def test_can_skip_unchanged_when_hash_model_and_dim_match():
    text = "fact card text"
    meta = ingest_metadata(
        text,
        embedding_model="mock",
        embedding_dimensions=_EMBED_DIM,
    )
    assert can_skip_unchanged(
        meta,
        text=text,
        embedding_model="mock",
        embedding_dimensions=_EMBED_DIM,
    )


def test_can_skip_unchanged_false_when_text_changes():
    meta = ingest_metadata(
        "old text",
        embedding_model="mock",
        embedding_dimensions=_EMBED_DIM,
    )
    assert not can_skip_unchanged(
        meta,
        text="new text",
        embedding_model="mock",
        embedding_dimensions=_EMBED_DIM,
    )


def test_can_skip_unchanged_false_when_model_changes():
    text = "fact card text"
    meta = ingest_metadata(
        text,
        embedding_model="mock",
        embedding_dimensions=_EMBED_DIM,
    )
    assert not can_skip_unchanged(
        meta,
        text=text,
        embedding_model="text-embedding-v4",
        embedding_dimensions=_EMBED_DIM,
    )


def test_can_skip_unchanged_false_when_dimensions_change():
    text = "fact card text"
    meta = ingest_metadata(
        text,
        embedding_model="text-embedding-v4",
        embedding_dimensions=384,
    )
    assert not can_skip_unchanged(
        meta,
        text=text,
        embedding_model="text-embedding-v4",
        embedding_dimensions=_EMBED_DIM,
    )
