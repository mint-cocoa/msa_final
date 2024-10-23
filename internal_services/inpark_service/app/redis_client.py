import aioredis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
QUEUE_TTL_SECONDS = 3600  # 예: 1시간
PRIORITY_QUEUE_KEY = "facilities_priority_queue"

redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

def get_queue_key(facility_id: str) -> str:
    return f"facility_queue:{facility_id}"

async def add_to_queue(facility_id: str, user_id: str):
    queue_key = get_queue_key(facility_id)
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.exists(queue_key).rpush(queue_key, user_id).expire(queue_key, QUEUE_TTL_SECONDS).execute()
        results = await pipe.execute()
        
    if results[0] == 0:  # 큐가 새로 생성된 경우
        await redis_client.zadd(PRIORITY_QUEUE_KEY, {facility_id: 1})
    else:
        await redis_client.zincrby(PRIORITY_QUEUE_KEY, 1, facility_id)

async def get_queue(facility_id: str):
    queue_key = get_queue_key(facility_id)
    return await redis_client.lrange(queue_key, 0, -1)

async def remove_from_queue(facility_id: str):
    queue_key = get_queue_key(facility_id)
    return await redis_client.lpop(queue_key)

async def queue_length(facility_id: str):
    queue_key = get_queue_key(facility_id)
    return await redis_client.llen(queue_key)

async def get_top_facilities(n: int = 10):
    return await redis_client.zrevrange(PRIORITY_QUEUE_KEY, 0, n-1, withscores=True)

async def remove_facility(facility_id: str):
    queue_key = get_queue_key(facility_id)
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.delete(queue_key).zrem(PRIORITY_QUEUE_KEY, facility_id).execute()
