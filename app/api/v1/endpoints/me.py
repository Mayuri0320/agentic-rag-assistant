"""Current-user authentication endpoint."""

from fastapi import APIRouter, Depends

from app.db.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)
