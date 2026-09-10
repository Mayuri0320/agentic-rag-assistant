"""Tests for semantic retrieval."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.ingestion.embeddings.base import EmbeddingProvider
from app.retrieval.models import RetrievalResult
from app.retrieval.retriever import SemanticRetriever
from app.vectorstore.chroma import ChromaVectorStore


class TestEmbeddingProvider(EmbeddingProvider):
    """Deterministic embedding provider for retrieval tests."""

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return 3

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Generate deterministic document embeddings."""
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """Generate deterministic query embedding."""
        return [1.0, 0.0, 0.0]


def create_store(
    tmp_path: Path,
) -> ChromaVectorStore:
    """Create an isolated test vector store."""
    return ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="retrieval_test",
    )


def seed_store(
    vector_store: ChromaVectorStore,
) -> None:
    """Add test chunks to the vector store."""
    vector_store.add_chunks(
        ids=[
            "document-1-chunk-0",
            "document-1-chunk-1",
        ],
        texts=[
            "Python is a programming language.",
            "FastAPI is a Python web framework.",
        ],
        embeddings=[
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
        ],
        metadatas=[
            {
                "document_id": "document-1",
                "user_id": "user-1",
                "chunk_index": 0,
            },
            {
                "document_id": "document-1",
                "user_id": "user-1",
                "chunk_index": 1,
            },
        ],
    )


def test_retrieves_relevant_chunks(
    tmp_path: Path,
) -> None:
    """The retriever should return semantically similar chunks."""
    vector_store = create_store(tmp_path)
    seed_store(vector_store)

    retriever = SemanticRetriever(
        embedding_provider=TestEmbeddingProvider(),
        vector_store=vector_store,
    )

    results = retriever.retrieve(
        query="Python programming",
        top_k=2,
    )

    assert len(results) == 2
    assert all(isinstance(result, RetrievalResult) for result in results)
    assert results[0].chunk_id == "document-1-chunk-0"
    assert results[0].text == "Python is a programming language."


def test_retrieval_passes_user_filter(
    tmp_path: Path,
) -> None:
    """User filtering should be passed through to the vector store."""
    vector_store = create_store(tmp_path)

    vector_store.add_chunks(
        ids=[
            "user-1-chunk",
            "user-2-chunk",
        ],
        texts=[
            "Private document for user one.",
            "Private document for user two.",
        ],
        embeddings=[
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        metadatas=[
            {
                "document_id": "document-1",
                "user_id": "user-1",
                "chunk_index": 0,
            },
            {
                "document_id": "document-2",
                "user_id": "user-2",
                "chunk_index": 0,
            },
        ],
    )

    retriever = SemanticRetriever(
        embedding_provider=TestEmbeddingProvider(),
        vector_store=vector_store,
    )

    results = retriever.retrieve(
        query="private document",
        top_k=5,
        user_id="user-1",
    )

    assert len(results) == 1
    assert results[0].metadata["user_id"] == "user-1"


def test_retrieval_passes_document_filter(
    tmp_path: Path,
) -> None:
    """Document filtering should be passed to the vector store."""
    vector_store = create_store(tmp_path)

    vector_store.add_chunks(
        ids=[
            "document-1-chunk",
            "document-2-chunk",
        ],
        texts=[
            "First document content.",
            "Second document content.",
        ],
        embeddings=[
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        metadatas=[
            {
                "document_id": "document-1",
                "user_id": "user-1",
                "chunk_index": 0,
            },
            {
                "document_id": "document-2",
                "user_id": "user-1",
                "chunk_index": 0,
            },
        ],
    )

    retriever = SemanticRetriever(
        embedding_provider=TestEmbeddingProvider(),
        vector_store=vector_store,
    )

    results = retriever.retrieve(
        query="document content",
        top_k=5,
        document_id="document-2",
    )

    assert len(results) == 1
    assert results[0].metadata["document_id"] == "document-2"


def test_rejects_empty_query(
    tmp_path: Path,
) -> None:
    """An empty query should be rejected."""
    retriever = SemanticRetriever(
        embedding_provider=TestEmbeddingProvider(),
        vector_store=create_store(tmp_path),
    )

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        retriever.retrieve(query="   ")


def test_rejects_invalid_top_k(
    tmp_path: Path,
) -> None:
    """A non-positive top_k should be rejected."""
    retriever = SemanticRetriever(
        embedding_provider=TestEmbeddingProvider(),
        vector_store=create_store(tmp_path),
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        retriever.retrieve(
            query="Python",
            top_k=0,
        )
