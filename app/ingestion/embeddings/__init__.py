"""Document embedding package."""

from app.ingestion.embeddings.base import EmbeddingProvider
from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.ingestion.embeddings.models import EmbeddedChunk

__all__ = [
    "EmbeddedChunk",
    "EmbeddingProvider",
    "MockEmbeddingProvider",
]
