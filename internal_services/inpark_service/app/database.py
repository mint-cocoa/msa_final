import aioredis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
