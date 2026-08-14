"""Authentication service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserRegister


class AuthenticationService:
    """Handle user registration and authentication."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the authentication service."""
        self.repository = UserRepository(session)

    async def register(self, user_data: UserRegister) -> TokenResponse:
        """Register a new user and return authentication tokens."""
        existing_user = await self.repository.get_by_email(str(user_data.email))

        if existing_user is not None:
            raise ValueError("User with this email already exists")

        hashed_password = hash_password(user_data.password)

        user = await self.repository.create(
            email=str(user_data.email),
            hashed_password=hashed_password,
        )

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        """Authenticate a user and return authentication tokens."""
        user = await self.repository.get_by_email(email)

        if user is None:
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise ValueError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise ValueError("Refresh token required")

        subject = payload.get("sub")

        if subject is None:
            raise ValueError("Invalid refresh token")

        try:
            user_id = int(subject)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid refresh token") from exc

        user = await self.repository.get_by_id(user_id)

        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")

        return create_access_token(user.id)
