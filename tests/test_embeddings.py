"""Tests for the embedding abstraction."""

import pytest

from app.ingestion.embeddings.mock import MockEmbeddingProvider


def test_mock_provider_generates_document_embeddings() -> None:
    """Provider should generate one vector per document."""
    provider = MockEmbeddingProvider(dimension=8)

    embeddings = provider.embed_documents(
        [
            "First document.",
            "Second document.",
        ]
    )

    assert len(embeddings) == 2
    assert all(len(embedding) == 8 for embedding in embeddings)


def test_mock_provider_generates_query_embedding() -> None:
    """Provider should generate a vector for a query."""
    provider = MockEmbeddingProvider(dimension=8)

    embedding = provider.embed_query("What is RAG?")

    assert len(embedding) == 8


def test_mock_provider_is_deterministic() -> None:
    """Identical input should produce identical vectors."""
    provider = MockEmbeddingProvider(dimension=8)

    first = provider.embed_query("Agentic RAG")
    second = provider.embed_query("Agentic RAG")

    assert first == second


def test_different_text_produces_different_embedding() -> None:
    """Different input should normally produce different vectors."""
    provider = MockEmbeddingProvider(dimension=8)

    first = provider.embed_query("Agentic RAG")
    second = provider.embed_query("Machine learning")

    assert first != second


def test_dimension_must_be_positive() -> None:
    """Invalid embedding dimensions should be rejected."""
    with pytest.raises(ValueError, match="dimension"):
        MockEmbeddingProvider(dimension=0)


def test_dimension_property() -> None:
    """Provider should expose its embedding dimension."""
    provider = MockEmbeddingProvider(dimension=16)

    assert provider.dimension == 16
