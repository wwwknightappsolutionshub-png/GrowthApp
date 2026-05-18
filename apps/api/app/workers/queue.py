import logging
from typing import Any
import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_pool = None


def get_redis_settings() -> RedisSettings:
    from urllib.parse import urlparse
    parsed = urlparse(settings.REDIS_URL)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


async def get_queue_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(get_redis_settings())
    return _pool


async def enqueue(function_name: str, _defer_by: int = 0, **kwargs: Any) -> None:
    """Enqueue a background job by function name."""
    try:
        pool = await get_queue_pool()
        if _defer_by:
            import asyncio
            await pool.enqueue_job(function_name, _defer_by=_defer_by, **kwargs)
        else:
            await pool.enqueue_job(function_name, **kwargs)
    except Exception as e:
        logger.error("Failed to enqueue job %s: %s", function_name, e)
