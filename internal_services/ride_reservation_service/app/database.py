import os
import aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

async def get_redis_client():
    return await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

redis_client = None

async def init_redis():
    global redis_client
    redis_client = await get_redis_client()

async def close_redis():
    if redis_client:
        await redis_client.close()
