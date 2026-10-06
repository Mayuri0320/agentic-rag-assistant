"""Coding assistant API endpoints."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.agent.dependencies import get_coding_service
from app.services.coding_service import CodingService

router = APIRouter(
    prefix="/coding",
    tags=["Coding Assistant"],
)

GENERATED_DIR = Path("data/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/generate")
async def generate_python_solution(
    file: UploadFile = File(...),
    instruction: str = Form(...),
    coding_service: CodingService = Depends(get_coding_service),
) -> dict[str, str]:
    """Generate a completed Python solution from an uploaded file."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".py"):
        raise HTTPException(
            status_code=400,
            detail="Only Python (.py) files are currently supported.",
        )

    try:
        content = await file.read()
        source_code = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The Python file must be UTF-8 encoded.",
        ) from exc

        
    try:
        result = coding_service.generate_solution(
            source_code=source_code,
            user_instruction=instruction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    generated_code = result["solution_code"]
    explanation = result["explanation"]

    output_filename = (
        f"{Path(file.filename).stem}_solution_{uuid4().hex[:8]}.py"
    )

    output_path = GENERATED_DIR / output_filename
    output_path.write_text(
        generated_code,
        encoding="utf-8",
    )

    return {
        "message": "Python solution generated successfully.",
        "filename": output_filename,
        "download_url": f"/coding/download/{output_filename}",
        "explanation": explanation,
    }



@router.get("/download/{filename}")
async def download_python_solution(filename: str) -> FileResponse:
    """Download a generated Python solution."""

    # Prevent path traversal.
    safe_filename = Path(filename).name

    file_path = GENERATED_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Generated file not found.",
        )

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="text/x-python",
    )