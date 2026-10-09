"""Coding assistant API endpoints."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.dependencies import get_coding_service
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.services.coding_service import CodingService
from app.services.conversation_service import ConversationService

router = APIRouter(
    prefix="/coding",
    tags=["Coding Assistant"],
)

GENERATED_DIR = Path("data/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def get_conversation_service(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationService:
    """Provide the conversation service."""
    return ConversationService(session)


@router.post("/generate")
async def generate_code_solution(
    file: UploadFile = File(...),
    instruction: str = Form(...),
    conversation_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    coding_service: CodingService = Depends(get_coding_service),
    conversation_service: ConversationService = Depends(
        get_conversation_service,
    ),
) -> dict[str, object]:
    """Generate code and persist the result in a conversation."""

    user_id = current_user.id

    # --------------------------------------------------------------
    # Conversation
    # --------------------------------------------------------------

    if conversation_id is None:
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            title=instruction[:100],
        )
    else:
        conversation = await conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

    # --------------------------------------------------------------
    # Validate input
    # --------------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    source_filename = Path(file.filename).name

    if not coding_service.detect_language_from_filename(source_filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported source file type. "
                "Please upload a supported programming-language file."
            ),
        )

    try:
        content = await file.read()
        source_code = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The source file must be UTF-8 encoded.",
        ) from exc

    if not source_code.strip():
        raise HTTPException(
            status_code=400,
            detail="The source-code file is empty.",
        )

    if not instruction.strip():
        raise HTTPException(
            status_code=400,
            detail="Instruction cannot be empty.",
        )

    # --------------------------------------------------------------
    # Persist user coding request
    # --------------------------------------------------------------

    user_message = (
        f"Coding request for `{source_filename}`:\n\n" f"{instruction.strip()}"
    )

    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=user_message,
    )

    # --------------------------------------------------------------
    # Generate code
    # --------------------------------------------------------------

    try:
        result = coding_service.generate_solution(
            source_code=source_code,
            user_instruction=instruction,
            source_filename=source_filename,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    generated_code = str(result["solution_code"]).strip()
    language = str(result["language"]).strip()
    extension = str(result["extension"]).strip()
    explanation = str(result["explanation"]).strip()

    if not generated_code:
        raise HTTPException(
            status_code=422,
            detail="The coding service returned empty generated code.",
        )

    # --------------------------------------------------------------
    # Save generated file
    # --------------------------------------------------------------

    output_filename = (
        f"{Path(source_filename).stem}_solution_{uuid4().hex[:8]}" f"{extension}"
    )

    output_path = GENERATED_DIR / output_filename

    output_path.write_text(
        generated_code,
        encoding="utf-8",
    )

    # --------------------------------------------------------------
    # Persist generated code artifact
    # --------------------------------------------------------------

    await conversation_service.add_code_artifact(
        conversation_id=conversation.id,
        user_id=user_id,
        filename=output_filename,
        language=language,
        source_code=generated_code,
    )

    # --------------------------------------------------------------
    # Persist assistant response
    # --------------------------------------------------------------

    assistant_message = (
        f"Generated {language.capitalize()} code successfully.\n\n"
        f"Generated file: {output_filename}\n\n"
        f"Explanation:\n{explanation}"
    )

    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content=assistant_message,
    )

    # --------------------------------------------------------------
    # Commit everything
    # --------------------------------------------------------------

    await conversation_service.commit()

    return {
        "message": (f"{language.capitalize()} solution generated successfully."),
        "filename": output_filename,
        "download_url": f"/coding/download/{output_filename}",
        "solution_code": generated_code,
        "explanation": explanation,
        "language": language,
        "conversation_id": conversation.id,
    }


@router.get("/download/{filename}")
async def download_code_solution(filename: str) -> FileResponse:
    """Download a generated source-code file."""

    # Prevent path traversal.
    safe_filename = Path(filename).name

    file_path = GENERATED_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Generated file not found.",
        )

    media_type = _get_media_type(file_path.suffix.lower())

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type,
    )


def _get_media_type(extension: str) -> str:
    """Return an appropriate MIME type for a source-code extension."""

    media_types = {
        ".py": "text/x-python",
        ".java": "text/x-java-source",
        ".js": "text/javascript",
        ".jsx": "text/javascript",
        ".ts": "text/typescript",
        ".tsx": "text/typescript",
        ".cpp": "text/x-c++src",
        ".cc": "text/x-c++src",
        ".cxx": "text/x-c++src",
        ".c": "text/x-c",
        ".h": "text/x-c",
        ".hpp": "text/x-c++src",
        ".cs": "text/plain",
        ".go": "text/plain",
        ".rs": "text/plain",
        ".php": "text/plain",
        ".rb": "text/plain",
        ".swift": "text/plain",
        ".kt": "text/plain",
        ".kts": "text/plain",
        ".scala": "text/plain",
        ".sql": "text/plain",
        ".sh": "text/plain",
        ".bash": "text/plain",
    }

    return media_types.get(extension, "text/plain")
