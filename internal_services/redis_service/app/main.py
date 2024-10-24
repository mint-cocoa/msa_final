from fastapi import FastAPI, HTTPException
import aioredis
import os
from .routes import router

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

@app.on_event("shutdown")
async def shutdown_event():
    # 애플리케이션 종료 시 Redis 연결 닫기
    await app.state.redis.close()

app.include_router(router, prefix="/api")  # ride_reservation_router 추가
