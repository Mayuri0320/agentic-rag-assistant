"""Redis service."""

import redis.asyncio as redis

from app.core.settings import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def check_redis_connection() -> bool:
    """Check whether Redis is available."""
    response = await redis_client.ping()
    return bool(response)
