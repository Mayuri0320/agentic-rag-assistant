"""Tests for secure semantic retrieval."""

from pathlib import Path

import pytest

from app.ingestion.chunking.text_chunker import TextChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import SemanticRetriever
from app.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def retriever(tmp_path: Path) -> SemanticRetriever:
    """Create a retriever backed by an isolated temporary Chroma store."""
    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="retrieval_test",
    )

    embedding_provider = MockEmbeddingProvider(dimension=32)

    pipeline = IngestionPipeline(
        loader_factory=DocumentLoaderFactory.default(),
        text_cleaner=TextCleaner(),
        text_chunker=TextChunker(
            chunk_size=1000,
            chunk_overlap=100,
        ),
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    user_a_file = tmp_path / "user_a.txt"
    user_a_file.write_text(
        "Machine learning enables systems to learn from data.",
        encoding="utf-8",
    )

    user_b_file = tmp_path / "user_b.txt"
    user_b_file.write_text(
        "Machine learning is used for medical image analysis.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=user_a_file,
        document_id="document-a",
        user_id="user-a",
        file_type="text/plain",
    )

    pipeline.ingest(
        file_path=user_b_file,
        document_id="document-b",
        user_id="user-b",
        file_type="text/plain",
    )

    return SemanticRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )


def test_retrieval_returns_only_current_users_chunks(
    retriever: SemanticRetriever,
) -> None:
    """A user must only receive chunks belonging to that user."""
    results = retriever.retrieve(
        query="machine learning",
        user_id="user-a",
        top_k=10,
    )

    assert results
    assert all(result.metadata["user_id"] == "user-a" for result in results)
    assert all(result.chunk_id.startswith("document-a-") for result in results)


def test_users_cannot_retrieve_each_others_chunks(
    retriever: SemanticRetriever,
) -> None:
    """Identical queries must not expose another user's documents."""
    user_a_results = retriever.retrieve(
        query="machine learning",
        user_id="user-a",
        top_k=10,
    )

    user_b_results = retriever.retrieve(
        query="machine learning",
        user_id="user-b",
        top_k=10,
    )

    assert user_a_results
    assert user_b_results

    user_a_ids = {result.chunk_id for result in user_a_results}
    user_b_ids = {result.chunk_id for result in user_b_results}

    assert user_a_ids.isdisjoint(user_b_ids)


def test_document_filter_cannot_escape_user_boundary(
    retriever: SemanticRetriever,
) -> None:
    """Requesting another user's document must return no results."""
    results = retriever.retrieve(
        query="machine learning",
        user_id="user-a",
        document_id="document-b",
        top_k=10,
    )

    assert results == []


def test_user_and_document_filter_work_together(
    retriever: SemanticRetriever,
) -> None:
    """A user can retrieve a specific document they own."""
    results = retriever.retrieve(
        query="machine learning",
        user_id="user-a",
        document_id="document-a",
        top_k=10,
    )

    assert results
    assert all(result.metadata["user_id"] == "user-a" for result in results)
    assert all(result.metadata["document_id"] == "document-a" for result in results)


def test_blank_user_id_is_rejected(
    retriever: SemanticRetriever,
) -> None:
    """Blank user identifiers must never permit unrestricted retrieval."""
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        retriever.retrieve(
            query="machine learning",
            user_id="   ",
        )


def test_query_is_required(
    retriever: SemanticRetriever,
) -> None:
    """Blank queries must be rejected."""
    with pytest.raises(ValueError, match="query cannot be empty"):
        retriever.retrieve(
            query="   ",
            user_id="user-a",
        )


def test_top_k_must_be_positive(
    retriever: SemanticRetriever,
) -> None:
    """top_k must be greater than zero."""
    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        retriever.retrieve(
            query="machine learning",
            user_id="user-a",
            top_k=0,
        )
