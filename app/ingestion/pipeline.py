"""Document ingestion pipeline."""

from dataclasses import dataclass
from pathlib import Path

from chromadb.api.types import Metadata

from app.ingestion.chunking.text_chunker import TextChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.embeddings.base import EmbeddingProvider
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.vectorstore.chroma import ChromaVectorStore


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Result returned after successfully ingesting a document."""

    document_id: str
    user_id: str
    chunk_count: int
    character_count: int


class IngestionPipeline:
    """Orchestrate document loading, cleaning, chunking, embedding, and storage."""

    def __init__(
        self,
        loader_factory: DocumentLoaderFactory,
        text_cleaner: TextCleaner,
        text_chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore,
    ) -> None:
        """Initialize the ingestion pipeline."""
        self._loader_factory = loader_factory
        self._text_cleaner = text_cleaner
        self._text_chunker = text_chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def ingest(
        self,
        *,
        file_path: str | Path,
        document_id: str,
        user_id: str,
        file_type: str,
    ) -> IngestionResult:
        """Ingest a document into the vector store."""
        path = Path(file_path)

        loader = self._loader_factory.get_loader(
            file_type=file_type,
            filename=path.name,
        )

        raw_text = loader.load(path)
        cleaned_text = self._text_cleaner.clean(raw_text)

        chunks = self._text_chunker.split_text(cleaned_text)

        if not chunks:
            return IngestionResult(
                document_id=document_id,
                user_id=user_id,
                chunk_count=0,
                character_count=len(cleaned_text),
            )

        chunk_texts = [chunk.text for chunk in chunks]

        embeddings = self._embedding_provider.embed_documents(chunk_texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding provider returned a different number "
                "of embeddings than chunks."
            )

        chunk_ids = [f"{document_id}-chunk-{chunk.chunk_index}" for chunk in chunks]

        metadatas: list[Metadata] = [
            {
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            for chunk in chunks
        ]

        self._vector_store.add_chunks(
            ids=chunk_ids,
            texts=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return IngestionResult(
            document_id=document_id,
            user_id=user_id,
            chunk_count=len(chunks),
            character_count=len(cleaned_text),
        )
