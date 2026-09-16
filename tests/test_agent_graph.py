"""Tests for the agentic RAG LangGraph workflow."""

from pathlib import Path

import pytest

from app.agent.graph import build_agent_graph
from app.agent.llm.mock import MockLLMProvider
from app.agent.nodes import AgentNodes
from app.agent.state import AgentState
from app.ingestion.chunking.text_chunker import TextChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import SemanticRetriever
from app.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def agent_graph(tmp_path: Path):
    """Create an isolated agent graph with test data."""
    vector_store = ChromaVectorStore(
        persist_directory=tmp_path / "chroma",
        collection_name="agent_graph_test",
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

    document = tmp_path / "document.txt"
    document.write_text(
        "Machine learning enables systems to learn from data.",
        encoding="utf-8",
    )

    pipeline.ingest(
        file_path=document,
        document_id="document-a",
        user_id="user-a",
        file_type="text/plain",
    )

    retriever = SemanticRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    llm_provider = MockLLMProvider()

    nodes = AgentNodes(
    retriever=retriever,
    llm_provider=llm_provider,
    )

    return build_agent_graph(nodes)


def test_agent_graph_retrieves_user_documents(agent_graph) -> None:
    """The graph should retrieve documents belonging to the current user."""
    state = AgentState(
        query="machine learning",
        user_id="user-a",
    )

    result = agent_graph.invoke(state)

    assert result["query"] == "machine learning"
    assert result["user_id"] == "user-a"
    assert result["retrieval_attempts"] == 1
    assert result["retrieved_chunks"]

    assert all(
        chunk["metadata"]["user_id"] == "user-a"
        for chunk in result["retrieved_chunks"]
    )


def test_agent_graph_does_not_cross_user_boundary(agent_graph) -> None:
    """The graph must not retrieve another user's documents."""
    state = AgentState(
        query="machine learning",
        user_id="user-b",
    )

    result = agent_graph.invoke(state)

    assert result["retrieved_chunks"] == []


def test_agent_graph_rejects_blank_query(agent_graph) -> None:
    """The planner should reject blank queries."""
    state = AgentState(
        query="   ",
        user_id="user-a",
    )

    with pytest.raises(ValueError, match="query cannot be empty"):
        agent_graph.invoke(state)


def test_agent_graph_rejects_blank_user_id(agent_graph) -> None:
    """The planner should reject blank user identifiers."""
    state = AgentState(
        query="machine learning",
        user_id="   ",
    )

    with pytest.raises(ValueError, match="user_id cannot be empty"):
        agent_graph.invoke(state)