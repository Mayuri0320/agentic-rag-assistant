"""Tests for the ChromaDB vector store."""

from pathlib import Path

import pytest

from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def vector_store(tmp_path: Path) -> ChromaVectorStore:
    """Create an isolated ChromaDB store for testing."""
    return ChromaVectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_chunks",
    )


@pytest.fixture
def embedding_provider() -> MockEmbeddingProvider:
    """Create a deterministic embedding provider."""
    return MockEmbeddingProvider(dimension=8)


def test_empty_store(
    vector_store: ChromaVectorStore,
) -> None:
    """A new store should contain no chunks."""
    assert vector_store.count() == 0


def test_add_chunks(
    vector_store: ChromaVectorStore,
) -> None:
    """Chunks should be stored successfully."""
    vector_store.add_chunks(
        ids=["chunk-1", "chunk-2"],
        texts=[
            "Agentic RAG uses retrieval.",
            "ChromaDB stores vectors.",
        ],
        embeddings=[
            [0.1] * 8,
            [0.2] * 8,
        ],
        metadatas=[
            {"user_id": 1, "document_id": 10},
            {"user_id": 1, "document_id": 10},
        ],
    )

    assert vector_store.count() == 2


def test_rejects_mismatched_lengths(
    vector_store: ChromaVectorStore,
) -> None:
    """Input collections must have matching lengths."""
    with pytest.raises(ValueError, match="same length"):
        vector_store.add_chunks(
            ids=["chunk-1"],
            texts=["text"],
            embeddings=[[0.1] * 8, [0.2] * 8],
            metadatas=[{"user_id": 1}],
        )


def test_search_returns_results(
    vector_store: ChromaVectorStore,
    embedding_provider: MockEmbeddingProvider,
) -> None:
    """Similarity search should return stored chunks."""
    texts = [
        "Agentic RAG retrieves relevant information.",
        "Machine learning models process data.",
    ]

    embeddings = embedding_provider.embed_documents(texts)

    vector_store.add_chunks(
        ids=["chunk-1", "chunk-2"],
        texts=texts,
        embeddings=embeddings,
        metadatas=[
            {"user_id": 1, "document_id": 10},
            {"user_id": 1, "document_id": 11},
        ],
    )

    query_embedding = embedding_provider.embed_query("Agentic RAG retrieval")

    results = vector_store.search(
        query_embedding=query_embedding,
        n_results=2,
    )

    assert len(results) == 2
    assert "id" in results[0]
    assert "text" in results[0]
    assert "metadata" in results[0]
    assert "distance" in results[0]


def test_search_filters_by_user(
    vector_store: ChromaVectorStore,
    embedding_provider: MockEmbeddingProvider,
) -> None:
    """Search should restrict results to the requested user."""
    texts = [
        "User one document.",
        "User two document.",
    ]

    embeddings = embedding_provider.embed_documents(texts)

    vector_store.add_chunks(
        ids=["user-1-chunk", "user-2-chunk"],
        texts=texts,
        embeddings=embeddings,
        metadatas=[
            {"user_id": 1, "document_id": 10},
            {"user_id": 2, "document_id": 20},
        ],
    )

    results = vector_store.search(
        query_embedding=embedding_provider.embed_query("document"),
        n_results=10,
        user_id=1,
    )

    assert len(results) == 1
    assert results[0]["metadata"]["user_id"] == 1


def test_search_filters_by_document(
    vector_store: ChromaVectorStore,
    embedding_provider: MockEmbeddingProvider,
) -> None:
    """Search should restrict results to the requested document."""
    texts = [
        "Document ten.",
        "Document twenty.",
    ]

    embeddings = embedding_provider.embed_documents(texts)

    vector_store.add_chunks(
        ids=["chunk-10", "chunk-20"],
        texts=texts,
        embeddings=embeddings,
        metadatas=[
            {"user_id": 1, "document_id": 10},
            {"user_id": 1, "document_id": 20},
        ],
    )

    results = vector_store.search(
        query_embedding=embedding_provider.embed_query("document"),
        n_results=10,
        document_id=20,
    )

    assert len(results) == 1
    assert results[0]["metadata"]["document_id"] == 20


def test_delete_document(
    vector_store: ChromaVectorStore,
) -> None:
    """Deleting a document should remove all its chunks."""
    vector_store.add_chunks(
        ids=["chunk-1", "chunk-2", "chunk-3"],
        texts=[
            "First chunk.",
            "Second chunk.",
            "Another document.",
        ],
        embeddings=[
            [0.1] * 8,
            [0.2] * 8,
            [0.3] * 8,
        ],
        metadatas=[
            {"user_id": 1, "document_id": 10},
            {"user_id": 1, "document_id": 10},
            {"user_id": 1, "document_id": 20},
        ],
    )

    vector_store.delete_document(document_id=10)

    assert vector_store.count() == 1


def test_invalid_result_count(
    vector_store: ChromaVectorStore,
) -> None:
    """Search should reject invalid result counts."""
    with pytest.raises(ValueError, match="n_results"):
        vector_store.search(
            query_embedding=[0.1] * 8,
            n_results=0,
        )
