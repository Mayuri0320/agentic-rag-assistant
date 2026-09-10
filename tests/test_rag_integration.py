"""End-to-end integration tests for the RAG ingestion and retrieval pipeline."""

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
def rag_components(
    tmp_path: Path,
) -> tuple[IngestionPipeline, SemanticRetriever, ChromaVectorStore]:
    """Create isolated ingestion and retrieval components."""
    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="rag_integration_test",
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

    retriever = SemanticRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    return pipeline, retriever, vector_store


def test_end_to_end_text_document_retrieval(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """A text document should be ingestible and retrievable end to end."""
    pipeline, retriever, vector_store = rag_components

    document = tmp_path / "knowledge.txt"
    document.write_text(
        """
        Retrieval augmented generation combines language models
        with external knowledge sources.

        A retrieval system first searches relevant information
        and then provides that information to a language model.
        """,
        encoding="utf-8",
    )

    result = pipeline.ingest(
        file_path=document,
        document_id="doc-001",
        user_id="user-001",
        file_type="text/plain",
    )

    assert result.document_id == "doc-001"
    assert result.user_id == "user-001"
    assert result.chunk_count > 0
    assert result.character_count > 0
    assert vector_store.count() == result.chunk_count

    retrieved = retriever.retrieve(
        query="retrieval augmented generation",
        user_id="user-001",
        top_k=5,
    )

    assert retrieved
    assert all(item.metadata["document_id"] == "doc-001" for item in retrieved)
    assert all(item.metadata["user_id"] == "user-001" for item in retrieved)


def test_multiple_documents_are_isolated_by_document_id(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """Retrieval can be restricted to one document."""
    pipeline, retriever, vector_store = rag_components

    first_document = tmp_path / "first.txt"
    first_document.write_text(
        "Python is widely used for machine learning applications.",
        encoding="utf-8",
    )

    second_document = tmp_path / "second.txt"
    second_document.write_text(
        "FastAPI is a modern Python framework for building APIs.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=first_document,
        document_id="doc-python",
        user_id="user-001",
        file_type="text/plain",
    )

    pipeline.ingest(
        file_path=second_document,
        document_id="doc-fastapi",
        user_id="user-001",
        file_type="text/plain",
    )

    assert vector_store.count() == 2

    results = retriever.retrieve(
        query="Python",
        user_id="user-001",
        document_id="doc-python",
        top_k=5,
    )

    assert results
    assert all(item.metadata["document_id"] == "doc-python" for item in results)


def test_cross_user_retrieval_is_blocked(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """A user must never retrieve another user's document."""
    pipeline, retriever, _ = rag_components

    private_document = tmp_path / "private.txt"
    private_document.write_text(
        "This information belongs exclusively to user alpha.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=private_document,
        document_id="private-doc",
        user_id="user-alpha",
        file_type="text/plain",
    )

    results = retriever.retrieve(
        query="private information",
        user_id="user-beta",
        top_k=5,
    )

    assert results == []


def test_cross_user_document_filter_is_blocked(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """Knowing another user's document ID must not bypass isolation."""
    pipeline, retriever, _ = rag_components

    private_document = tmp_path / "private.txt"
    private_document.write_text(
        "Confidential information for user alpha.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=private_document,
        document_id="alpha-document",
        user_id="user-alpha",
        file_type="text/plain",
    )

    results = retriever.retrieve(
        query="confidential information",
        user_id="user-beta",
        document_id="alpha-document",
        top_k=5,
    )

    assert results == []


def test_document_deletion_removes_retrievable_chunks(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """Deleting a document should remove its vector chunks."""
    pipeline, retriever, vector_store = rag_components

    document = tmp_path / "delete-me.txt"
    document.write_text(
        "This document will be deleted from the vector store.",
        encoding="utf-8",
    )

    result = pipeline.ingest(
        file_path=document,
        document_id="delete-doc",
        user_id="user-001",
        file_type="text/plain",
    )

    assert result.chunk_count > 0
    assert vector_store.count() == result.chunk_count

    before_delete = retriever.retrieve(
        query="document deleted vector store",
        user_id="user-001",
        document_id="delete-doc",
        top_k=5,
    )

    assert before_delete

    vector_store.delete_document("delete-doc")

    assert vector_store.count() == 0

    after_delete = retriever.retrieve(
        query="document deleted vector store",
        user_id="user-001",
        document_id="delete-doc",
        top_k=5,
    )

    assert after_delete == []


def test_empty_document_does_not_create_vectors(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """An empty document should not create vector-store entries."""
    pipeline, _, vector_store = rag_components

    document = tmp_path / "empty.txt"
    document.write_text("", encoding="utf-8")

    result = pipeline.ingest(
        file_path=document,
        document_id="empty-doc",
        user_id="user-001",
        file_type="text/plain",
    )

    assert result.chunk_count == 0
    assert result.character_count == 0
    assert vector_store.count() == 0


def test_cleaning_occurs_before_retrieval(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """Text cleaning should happen before content reaches retrieval."""
    pipeline, retriever, _ = rag_components

    document = tmp_path / "messy.txt"
    document.write_text(
        "Machine   learning\r\n\r\n" "is used for data analysis.\u0000",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=document,
        document_id="cleaning-doc",
        user_id="user-001",
        file_type="text/plain",
    )

    results = retriever.retrieve(
        query="machine learning",
        user_id="user-001",
        document_id="cleaning-doc",
        top_k=5,
    )

    assert results
    assert all("\x00" not in item.text for item in results)
    assert all("Machine" in item.text or "machine" in item.text for item in results)


def test_metadata_remains_consistent_through_pipeline(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
    tmp_path: Path,
) -> None:
    """Document ownership metadata should survive the full pipeline."""
    pipeline, retriever, _ = rag_components

    document = tmp_path / "metadata.txt"
    document.write_text(
        "Metadata must remain attached to every document chunk.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=document,
        document_id="metadata-doc",
        user_id="metadata-user",
        file_type="text/plain",
    )

    results = retriever.retrieve(
        query="metadata document chunk",
        user_id="metadata-user",
        top_k=5,
    )

    assert results

    for result in results:
        assert result.metadata["document_id"] == "metadata-doc"
        assert result.metadata["user_id"] == "metadata-user"
        assert isinstance(result.metadata["chunk_index"], int)
        assert isinstance(result.metadata["start_char"], int)
        assert isinstance(result.metadata["end_char"], int)


def test_user_cannot_use_blank_identifier_for_retrieval(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
) -> None:
    """Blank user identifiers must always be rejected."""
    _, retriever, _ = rag_components

    with pytest.raises(ValueError, match="user_id cannot be empty"):
        retriever.retrieve(
            query="anything",
            user_id=" ",
        )


def test_retrieval_rejects_invalid_top_k(
    rag_components: tuple[
        IngestionPipeline,
        SemanticRetriever,
        ChromaVectorStore,
    ],
) -> None:
    """Invalid retrieval limits must be rejected."""
    _, retriever, _ = rag_components

    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        retriever.retrieve(
            query="anything",
            user_id="user-001",
            top_k=0,
        )
