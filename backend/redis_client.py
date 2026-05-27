import redis.asyncio as redis

from backend.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def init_redis() -> None:
    """Verify Redis connectivity."""
    await redis_client.ping()


async def close_redis() -> None:
    """Close Redis connection pool."""
    await redis_client.close()
