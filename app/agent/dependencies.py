"""Dependencies for constructing the agentic RAG workflow."""

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from app.agent.graph import build_agent_graph
from app.agent.llm.base import LLMProvider
from app.agent.llm.factory import LLMProviderFactory
from app.agent.nodes import AgentNodes
from app.core.settings import get_settings
from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.retrieval.retriever import SemanticRetriever
from app.vectorstore.chroma import ChromaVectorStore


@lru_cache
def get_vector_store() -> ChromaVectorStore:
    """Return the application vector store."""
    settings = get_settings()

    return ChromaVectorStore(
        persist_directory=settings.chroma_persist_directory,
        collection_name="document_chunks",
    )


@lru_cache
def get_embedding_provider() -> MockEmbeddingProvider:
    """Return the application embedding provider."""
    return MockEmbeddingProvider(dimension=32)


@lru_cache
def get_semantic_retriever() -> SemanticRetriever:
    """Create the semantic retriever used by the agent."""
    return SemanticRetriever(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Create the configured default language model provider."""
    settings = get_settings()

    return LLMProviderFactory.create(
        provider=settings.llm_provider,
        api_key=settings.openai_api_key,
        model=settings.llm_model,
    )


@lru_cache
def get_openai_provider() -> LLMProvider:
    """Create the OpenAI language model provider."""
    settings = get_settings()

    return LLMProviderFactory.create(
        provider="openai",
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )


@lru_cache
def get_gemini_provider() -> LLMProvider:
    """Create the Gemini language model provider."""
    settings = get_settings()

    return LLMProviderFactory.create(
        provider="gemini",
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )


@lru_cache
def get_agent_graph() -> CompiledStateGraph:
    """Build and cache the application agent graph."""
    nodes = AgentNodes(
        retriever=get_semantic_retriever(),
        llm_provider=get_llm_provider(),
        openai_provider=get_openai_provider(),
        gemini_provider=get_gemini_provider(),
    )

    return build_agent_graph(nodes)