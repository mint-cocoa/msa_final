from fastapi import FastAPI, HTTPException
import os
import aioredis
import aio_pika
import asyncio
from .routes import router
from .redis_pubsub import start_pubsub_listener

app = FastAPI(
    title="Redis Service",
    description="Service for managing redis",
    version="1.0.0",
    root_path="/redis"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@app.on_event("startup")
async def startup_event():
    # Redis 클라이언트를 애플리케이션 상태에 저장
    app.state.redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    
    # Redis PubSub 리스너 시작
    asyncio.create_task(start_pubsub_listener(app.state.redis))
    asyncio.create_task(run_consumer())

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()

app.include_router(router, prefix="/api")
