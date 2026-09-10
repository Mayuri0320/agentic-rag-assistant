"""Document API endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.ingestion.chunking.text_chunker import TextChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.embeddings.mock import MockEmbeddingProvider
from app.ingestion.loaders.factory import DocumentLoaderFactory
from app.ingestion.pipeline import IngestionPipeline
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    IngestionResponse,
)
from app.services.document_service import DocumentService
from app.storage.document_storage import DocumentStorage
from app.vectorstore.chroma import ChromaVectorStore

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_vector_store() -> ChromaVectorStore:
    """Create the application vector store."""
    settings = get_settings()

    return ChromaVectorStore(
        persist_directory=settings.chroma_persist_directory,
        collection_name="document_chunks",
    )


def get_ingestion_pipeline(
    vector_store: ChromaVectorStore = Depends(get_vector_store),
) -> IngestionPipeline:
    """Create the document ingestion pipeline."""
    return IngestionPipeline(
        loader_factory=DocumentLoaderFactory.default(),
        text_cleaner=TextCleaner(),
        text_chunker=TextChunker(
            chunk_size=1000,
            chunk_overlap=200,
        ),
        embedding_provider=MockEmbeddingProvider(
            dimension=32,
        ),
        vector_store=vector_store,
    )


def get_document_service(
    session: AsyncSession = Depends(get_db_session),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
    ingestion_pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> DocumentService:
    """Create a document service."""
    settings = get_settings()

    storage = DocumentStorage(
        settings.document_storage_directory,
    )

    return DocumentService(
        session=session,
        storage=storage,
        ingestion_pipeline=ingestion_pipeline,
        vector_store=vector_store,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """Upload, ingest, and index a document."""
    content = await file.read()

    try:
        document, ingestion_result = await service.create_document(
            user_id=current_user.id,
            filename=file.filename or "unknown",
            file_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if ingestion_result is None:
        ingestion_response = IngestionResponse(
            status="not_processed",
            chunk_count=0,
            character_count=0,
        )
    else:
        ingestion_response = IngestionResponse(
            status="completed",
            chunk_count=ingestion_result.chunk_count,
            character_count=ingestion_result.character_count,
        )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(document),
        ingestion=ingestion_response,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List documents belonging to the current user."""
    documents = await service.list_documents(current_user.id)

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(document) for document in documents],
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get a document belonging to the current user."""
    try:
        document = await service.get_document(
            document_id=document_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document belonging to the current user."""
    try:
        await service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
