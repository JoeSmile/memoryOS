import hashlib
import math

from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings, get_settings


def _mock_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic L2-normalized vector from text (Harness/CI without API key)."""
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for i in range(0, len(block) - 3, 4):
            if len(values) >= dimensions:
                break
            n = int.from_bytes(block[i : i + 4], "big")
            values.append((n / 2**32) * 2 - 1)
        counter += 1

    norm = math.sqrt(sum(x * x for x in values))
    if norm == 0:
        return values
    return [x / norm for x in values]


class EmbeddingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._live: OpenAIEmbeddings | None = None
        if not self._settings.use_mock_embedding:
            kwargs: dict[str, object] = {
                "model": self._settings.embedding_model,
                "dimensions": self._settings.embedding_dimensions,
                # DashScope expects raw strings, not tiktoken token ids.
                "check_embedding_ctx_length": False,
            }
            if self._settings.openai_api_key:
                kwargs["api_key"] = self._settings.openai_api_key
            base_url = (
                self._settings.embedding_api_base or self._settings.openai_api_base
            )
            if base_url:
                kwargs["base_url"] = base_url
            self._live = OpenAIEmbeddings(**kwargs)

    @property
    def use_mock(self) -> bool:
        return self._settings.use_mock_embedding

    @property
    def model_label(self) -> str:
        """Stored on documents.metadata to invalidate skip when model/mode changes."""
        if self.use_mock:
            return "mock"
        return self._settings.embedding_model

    @property
    def embedding_dimensions(self) -> int:
        return self._settings.embedding_dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.use_mock:
            dim = self._settings.embedding_dimensions
            return [_mock_embedding(text, dim) for text in texts]
        assert self._live is not None
        vectors = await self._live.aembed_documents(texts)
        self._validate_batch(vectors)
        return vectors

    async def embed_query(self, query: str) -> list[float]:
        if self.use_mock:
            return _mock_embedding(query, self._settings.embedding_dimensions)
        assert self._live is not None
        vector = await self._live.aembed_query(query)
        self._validate_one(vector)
        return vector

    def _validate_one(self, vector: list[float]) -> None:
        expected = self._settings.embedding_dimensions
        if len(vector) != expected:
            raise ValueError(
                f"embedding dimension mismatch: got {len(vector)}, expected {expected}"
            )

    def _validate_batch(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            self._validate_one(vector)
