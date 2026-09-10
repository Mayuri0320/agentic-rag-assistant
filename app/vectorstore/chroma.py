from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from chromadb.api.types import Metadata, QueryResult

from app.ingestion.embeddings.models import EmbeddedChunk


class ChromaVectorStore:
    """Persistent ChromaDB-backed vector store."""

    def __init__(
        self,
        persist_directory: str | Path,
        collection_name: str = "document_chunks",
    ) -> None:
        """Initialize the persistent ChromaDB collection."""
        persist_path = Path(persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(persist_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[Metadata],
    ) -> None:
        """Add or update document chunks in the vector store."""
        if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError(
                "ids, texts, embeddings, and metadatas must have " "the same length."
            )

        embedding_array = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embedding_array,
            metadatas=metadatas,
        )

    def add_embedded_chunks(
        self,
        chunks: list[EmbeddedChunk],
        metadatas: list[Metadata],
    ) -> None:
        """Add embedded chunks to the vector store."""
        if len(chunks) != len(metadatas):
            raise ValueError("chunks and metadatas must have the same length.")

        self.add_chunks(
            ids=[f"chunk-{chunk.chunk_index}" for chunk in chunks],
            texts=[chunk.text for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        user_id: str | None = None,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for the most similar document chunks."""
        if n_results <= 0:
            raise ValueError("n_results must be greater than zero.")

        where = self._build_filter(
            user_id=user_id,
            document_id=document_id,
        )

        query_vector = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        results: QueryResult = self._collection.query(
            query_embeddings=query_vector,
            n_results=n_results,
            where=where,
        )

        return self._format_search_results(results)

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """Delete all chunks belonging to a document."""
        self._collection.delete(
            where={"document_id": document_id},
        )

    def count(self) -> int:
        """Return the number of stored chunks."""
        return self._collection.count()

    @staticmethod
    def _build_filter(
        user_id: str | None = None,
        document_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a Chroma metadata filter."""
        conditions: list[dict[str, str]] = []

        if user_id is not None:
            conditions.append({"user_id": user_id})

        if document_id is not None:
            conditions.append({"document_id": document_id})

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {
            "$and": conditions,
        }

    @staticmethod
    def _format_search_results(
        results: QueryResult,
    ) -> list[dict[str, Any]]:
        """Convert Chroma query results into application-friendly data."""
        ids = results["ids"]
        documents = results.get("documents")
        metadatas = results.get("metadatas")
        distances = results.get("distances")

        formatted: list[dict[str, Any]] = []

        for index, result_id in enumerate(ids[0]):
            formatted.append(
                {
                    "id": result_id,
                    "text": (documents[0][index] if documents else None),
                    "metadata": (metadatas[0][index] if metadatas else None),
                    "distance": (distances[0][index] if distances else None),
                }
            )

        return formatted
