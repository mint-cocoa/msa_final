from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import aioredis
import os
import asyncio
import httpx
from datetime import datetime, time
from typing import List

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
FACILITY_SERVICE_URL = os.getenv("FACILITY_SERVICE_URL", "http://facility_service:8000")
UPDATE_INTERVAL = 300  # 5분마다 업데이트

redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

class QueueItem(BaseModel):
    facility_id: str
    user_id: str

class Facility(BaseModel):
    id: str
    name: str
    max_queue_capacity: int
    is_operating: bool
    open_time: time
    close_time: time

class EnterFacilityRequest(BaseModel):
    facility_id: str
    entered_count: int

async def update_facility_queues():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{FACILITY_SERVICE_URL}/facilities/operating")
                if response.status_code == 200:
                    facilities = [Facility(**facility) for facility in response.json()]
                    current_time = datetime.now().time()
                    
                    for facility in facilities:
                        queue_key = f"facility_queue:{facility.id}"
                        
                        if facility.open_time <= current_time <= facility.close_time:
                            await redis_client.expire(queue_key, 86400)
                            await redis_client.set(f"{queue_key}:max_capacity", facility.max_queue_capacity)
                        else:
                            await redis_client.delete(queue_key)
                            await redis_client.delete(f"{queue_key}:max_capacity")
                    
                    print(f"Updated {len(facilities)} facility queues")
                else:
                    print(f"Failed to fetch operating facilities: {response.status_code}")
        except Exception as e:
            print(f"Error updating facility queues: {str(e)}")
        
        await asyncio.sleep(UPDATE_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_facility_queues())

@app.post("/queue")
async def add_to_queue(item: QueueItem):
    queue_key = f"facility_queue:{item.facility_id}"
    max_capacity = await redis_client.get(f"{queue_key}:max_capacity")
    
    if max_capacity is None:
        raise HTTPException(status_code=400, detail="Facility queue not available")
    
    current_queue_length = await redis_client.llen(queue_key)
    if current_queue_length >= int(max_capacity):
        raise HTTPException(status_code=400, detail="Queue is full")
    
    await redis_client.rpush(queue_key, item.user_id)
    return {"message": "Added to queue successfully"}

@app.get("/queue/{facility_id}")
async def get_queue(facility_id: str):
    queue_key = f"facility_queue:{facility_id}"
    queue = await redis_client.lrange(queue_key, 0, -1)
    max_capacity = await redis_client.get(f"{queue_key}:max_capacity")
    current_length = len(queue)
    return {
        "facility_id": facility_id,
        "queue": queue,
        "length": current_length,
        "max_capacity": max_capacity,
        "available_spots": int(max_capacity) - current_length if max_capacity else None
    }

@app.delete("/queue/{facility_id}")
async def remove_facility(facility_id: str):
    queue_key = f"facility_queue:{facility_id}"
    await redis_client.delete(queue_key)
    await redis_client.delete(f"{queue_key}:max_capacity")
    return {"message": "Facility removed from queue"}

@app.post("/enter_facility")
async def enter_facility(request: EnterFacilityRequest):
    queue_key = f"facility_queue:{request.facility_id}"
    
    entered_users = []
    for _ in range(request.entered_count):
        user = await redis_client.lpop(queue_key)
        if user:
            entered_users.append(user)
        else:
            break
    
    return {
        "facility_id": request.facility_id,
        "entered_count": len(entered_users),
        "entered_users": entered_users
    }

# 기존의 다른 API Gateway 라우트들...
