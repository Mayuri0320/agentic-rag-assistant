"""Deterministic embedding provider for tests."""

import hashlib
from collections.abc import Sequence

from app.ingestion.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Generate deterministic embeddings without an external API."""

    def __init__(self, *, dimension: int = 8) -> None:
        """Initialize the mock provider."""
        if dimension <= 0:
            raise ValueError("dimension must be greater than zero")

        self._dimension = dimension

    @property
    def dimension(self) -> int:
        """Return embedding dimensionality."""
        return self._dimension

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Generate deterministic embeddings for documents."""
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Generate a deterministic query embedding."""
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        """Generate a deterministic vector from text."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()

        values: list[float] = []

        for index in range(self._dimension):
            byte_value = digest[index % len(digest)]
            values.append(byte_value / 255.0)

        return values
