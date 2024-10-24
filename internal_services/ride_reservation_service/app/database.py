import os
import aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

async def get_redis_client():
    return await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)