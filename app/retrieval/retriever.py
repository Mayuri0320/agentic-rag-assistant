"""Semantic retrieval with mandatory user isolation."""

from app.ingestion.embeddings.base import EmbeddingProvider
from app.retrieval.models import RetrievalResult
from app.vectorstore.chroma import ChromaVectorStore


class SemanticRetriever:
    """Retrieve semantically similar document chunks for a specific user."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve chunks while enforcing user-level data isolation.

        Args:
            query: Natural-language search query.
            user_id: ID of the authenticated user. Required.
            top_k: Maximum number of chunks to return.
            document_id: Optional document restriction.

        Returns:
            Matching chunks belonging to the requested user.

        Raises:
            ValueError: If query/user_id is empty or top_k is invalid.
        """
        normalized_query = query.strip()
        normalized_user_id = user_id.strip()

        if not normalized_query:
            raise ValueError("query cannot be empty")

        if not normalized_user_id:
            raise ValueError("user_id cannot be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        query_embedding = self.embedding_provider.embed_query(normalized_query)

        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k,
            user_id=normalized_user_id,
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
