from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aioredis
import os

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
QUEUE_TTL_SECONDS = 3600  # 예: 1시간
PRIORITY_QUEUE_KEY = "facilities_priority_queue"

redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

class QueueItem(BaseModel):
    facility_id: str
    user_id: str

@app.post("/queue")
async def add_to_queue(item: QueueItem):
    queue_key = f"facility_queue:{item.facility_id}"
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.exists(queue_key).rpush(queue_key, item.user_id).expire(queue_key, QUEUE_TTL_SECONDS).execute()
        results = await pipe.execute()
        
    if results[0] == 0:  # 큐가 새로 생성된 경우
        await redis_client.zadd(PRIORITY_QUEUE_KEY, {item.facility_id: 1})
    else:
        await redis_client.zincrby(PRIORITY_QUEUE_KEY, 1, item.facility_id)
    
    return {"message": "Added to queue successfully"}

@app.get("/queue/{facility_id}")
async def get_queue(facility_id: str):
    queue_key = f"facility_queue:{facility_id}"
    queue = await redis_client.lrange(queue_key, 0, -1)
    return {"facility_id": facility_id, "queue": queue, "length": len(queue)}

@app.get("/top_facilities")
async def get_top_facilities(n: int = 10):
    top_facilities = await redis_client.zrevrange(PRIORITY_QUEUE_KEY, 0, n-1, withscores=True)
    return {"top_facilities": top_facilities}

@app.delete("/queue/{facility_id}")
async def remove_facility(facility_id: str):
    queue_key = f"facility_queue:{facility_id}"
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.delete(queue_key).zrem(PRIORITY_QUEUE_KEY, facility_id).execute()
    return {"message": "Facility removed from queue"}

@app.post("/guest")
async def add_guest(guest_info: dict):
    guest_id = guest_info.pop("id", None)
    if not guest_id:
        raise HTTPException(status_code=400, detail="Guest ID is required")
    await redis_client.hset(f"guest:{guest_id}", mapping=guest_info)
    return {"message": "Guest added successfully"}

@app.get("/guest/{guest_id}")
async def get_guest(guest_id: str):
    guest_info = await redis_client.hgetall(f"guest:{guest_id}")
    if not guest_info:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest_info

@app.delete("/guest/{guest_id}")
async def remove_guest(guest_id: str):
    result = await redis_client.delete(f"guest:{guest_id}")
    if result == 0:
        raise HTTPException(status_code=404, detail="Guest not found")
    return {"message": "Guest removed successfully"}

@app.get("/guest_count")
async def get_guest_count():
    guest_keys = await redis_client.keys("guest:*")
    return {"guest_count": len(guest_keys)}
