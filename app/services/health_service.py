"""Health check service."""

from app.db.connection import check_database_connection
from app.services.redis_service import check_redis_connection


class HealthService:
    """Service for checking application dependencies."""

    async def check_database(self) -> bool:
        """Check PostgreSQL availability."""
        return await check_database_connection()

    async def check_redis(self) -> bool:
        """Check Redis availability."""
        return await check_redis_connection()

    async def check_dependencies(self) -> dict[str, bool]:
        """Check all external dependencies."""
        database_ok = await self.check_database()
        redis_ok = await self.check_redis()

        return {
            "database": database_ok,
            "redis": redis_ok,
        }
