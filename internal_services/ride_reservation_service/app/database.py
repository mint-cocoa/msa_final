import os
import aioredis
import logging
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

class Database:
    redis_client: Optional[aioredis.Redis] = None
    
    @classmethod
    async def connect_db(cls):
        if cls.redis_client is None:
            cls.redis_client = await aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logging.info("Connected to Redis")
    
    @classmethod
    async def close_db(cls):
        if cls.redis_client is not None:
            await cls.redis_client.close()
            cls.redis_client = None
            logging.info("Closed Redis connection")

async def get_redis():
    if Database.redis_client is None:
        await Database.connect_db()
    return Database.redis_client