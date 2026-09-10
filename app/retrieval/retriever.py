"""Semantic document retrieval."""

from app.ingestion.embeddings.base import EmbeddingProvider
from app.retrieval.models import RetrievalResult
from app.vectorstore.chroma import ChromaVectorStore


class SemanticRetriever:
    """Retrieve relevant document chunks using semantic similarity."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore,
    ) -> None:
        """Initialize the semantic retriever."""
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(
        self,
        *,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        document_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve the most relevant chunks for a query."""
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("query cannot be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        query_embedding = self._embedding_provider.embed_query(normalized_query)

        results = self._vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k,
            user_id=user_id,
            document_id=document_id,
        )

        return [
            RetrievalResult(
                chunk_id=result["id"],
                text=result["text"] or "",
                metadata=result["metadata"] or {},
                distance=result["distance"],
            )
            for result in results
        ]
