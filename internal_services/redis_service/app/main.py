from fastapi import FastAPI, HTTPException
import aioredis
import os

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@app.on_event("startup")
async def startup_event():
    app.state.redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()

@app.get("/queue_position/{ride_id}/{user_id}")
async def get_queue_position(ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    position = await app.state.redis.zrank(queue_key, user_id)
    if position is None:
        raise HTTPException(status_code=404, detail="User not in queue")
    return {"position": position + 1}  # 1-based index

@app.post("/dequeue/front/{ride_id}/{count}")
async def dequeue_users(ride_id: str, count: int):
    queue_key = f"ride_queue:{ride_id}"
    # 큐의 맨 앞에서 특정 수(count)만큼 사용자 ID 가져오기
    user_ids = await app.state.redis.zrange(queue_key, 0, count - 1)
    
    if not user_ids:
        raise HTTPException(status_code=404, detail="Queue is empty or not enough users")
    
    # 가져온 사용자 ID 제거
    for user_id in user_ids:
        await app.state.redis.zrem(queue_key, user_id)
    
    return {"message": f"{len(user_ids)} users removed from queue for ride {ride_id}"}
