"""Tests for the document ingestion pipeline."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.ingestion.chunking.text_chunker import TextChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.embeddings.base import EmbeddingProvider
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.ingestion.pipeline import IngestionPipeline
from app.vectorstore.chroma import ChromaVectorStore


class TestEmbeddingProvider(EmbeddingProvider):
    """Simple deterministic embedding provider for pipeline tests."""

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return 3

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Return deterministic embeddings for documents."""
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        """Return a deterministic query embedding."""
        return [1.0, 0.0, 0.0]


class MismatchedEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that intentionally returns the wrong count."""

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return 3

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Return fewer embeddings than requested."""
        if not texts:
            return []

        return [[1.0, 0.0, 0.0] for _ in texts[:-1]]

    def embed_query(self, text: str) -> list[float]:
        """Return a deterministic query embedding."""
        return [1.0, 0.0, 0.0]


def create_pipeline(
    vector_store: ChromaVectorStore,
    embedding_provider: EmbeddingProvider | None = None,
) -> IngestionPipeline:
    """Create a pipeline with test dependencies."""
    return IngestionPipeline(
        loader_factory=DocumentLoaderFactory.default(),
        text_cleaner=TextCleaner(),
        text_chunker=TextChunker(
            chunk_size=100,
            chunk_overlap=20,
        ),
        embedding_provider=(
            embedding_provider
            if embedding_provider is not None
            else TestEmbeddingProvider()
        ),
        vector_store=vector_store,
    )


def test_ingests_text_document(
    tmp_path: Path,
) -> None:
    """A text document should be loaded, processed, embedded, and stored."""
    document_path = tmp_path / "example.txt"
    document_path.write_text(
        "This is the first paragraph.\n\n"
        "This is the second paragraph containing useful information.",
        encoding="utf-8",
    )

    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_ingestion",
    )

    pipeline = create_pipeline(vector_store)

    result = pipeline.ingest(
        file_path=document_path,
        document_id="document-123",
        user_id="user-456",
        file_type="text/plain",
    )

    assert result.document_id == "document-123"
    assert result.user_id == "user-456"
    assert result.chunk_count > 0
    assert result.character_count > 0
    assert vector_store.count() == result.chunk_count


def test_ingested_chunks_have_document_and_user_metadata(
    tmp_path: Path,
) -> None:
    """Stored chunks should contain document and user ownership metadata."""
    document_path = tmp_path / "metadata.txt"
    document_path.write_text(
        "This document contains metadata that should be preserved.",
        encoding="utf-8",
    )

    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_metadata",
    )

    pipeline = create_pipeline(vector_store)

    pipeline.ingest(
        file_path=document_path,
        document_id="document-123",
        user_id="user-456",
        file_type="text/plain",
    )

    results = vector_store.search(
        query_embedding=[1.0, 0.0, 0.0],
        user_id="user-456",
        document_id="document-123",
    )

    assert results
    assert results[0]["metadata"]["document_id"] == "document-123"
    assert results[0]["metadata"]["user_id"] == "user-456"
    assert results[0]["metadata"]["chunk_index"] == 0


def test_empty_document_produces_no_chunks(
    tmp_path: Path,
) -> None:
    """An empty document should complete without creating vector chunks."""
    document_path = tmp_path / "empty.txt"
    document_path.write_text(
        "",
        encoding="utf-8",
    )

    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_empty",
    )

    pipeline = create_pipeline(vector_store)

    result = pipeline.ingest(
        file_path=document_path,
        document_id="document-empty",
        user_id="user-123",
        file_type="text/plain",
    )

    assert result.chunk_count == 0
    assert result.character_count == 0
    assert vector_store.count() == 0


def test_embedding_count_must_match_chunk_count(
    tmp_path: Path,
) -> None:
    """The pipeline should reject an incorrect embedding count."""
    document_path = tmp_path / "mismatch.txt"
    document_path.write_text(
        "This document is long enough to produce content for embedding.",
        encoding="utf-8",
    )

    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_mismatch",
    )

    pipeline = create_pipeline(
        vector_store,
        embedding_provider=MismatchedEmbeddingProvider(),
    )

    with pytest.raises(
        ValueError,
        match="different number of embeddings",
    ):
        pipeline.ingest(
            file_path=document_path,
            document_id="document-mismatch",
            user_id="user-123",
            file_type="text/plain",
        )

    assert vector_store.count() == 0


def test_pipeline_uses_file_extension_fallback(
    tmp_path: Path,
) -> None:
    """The loader factory should fall back to the file extension."""
    document_path = tmp_path / "fallback.txt"
    document_path.write_text(
        "Extension based document loading.",
        encoding="utf-8",
    )

    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="test_extension",
    )

    pipeline = create_pipeline(vector_store)

    result = pipeline.ingest(
        file_path=document_path,
        document_id="document-fallback",
        user_id="user-123",
        file_type="application/octet-stream",
    )

    assert result.chunk_count == 1
    assert vector_store.count() == 1
