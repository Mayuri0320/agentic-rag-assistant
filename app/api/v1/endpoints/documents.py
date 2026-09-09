"""Document API endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_service import DocumentService
from app.storage.document_storage import DocumentStorage

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_document_service(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentService:
    """Create a document service."""
    settings = get_settings()

    storage = DocumentStorage(
        settings.document_storage_directory,
    )

    return DocumentService(
        session=session,
        storage=storage,
    )


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Upload a document."""
    content = await file.read()

    try:
        document = await service.create_document(
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

    return DocumentResponse.model_validate(document)


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
