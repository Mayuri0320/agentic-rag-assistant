"""Database connection utilities."""

from typing import cast

from sqlalchemy import text

from app.db.session import engine


async def check_database_connection() -> bool:
    """Check whether the database connection is available."""
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        value = cast(int, result.scalar_one())
        return value == 1
