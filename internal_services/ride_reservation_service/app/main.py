import os
from fastapi import FastAPI
import aioredis
from .routes import router as ride_reservation_router
from .database import Database

app = FastAPI(
    title="Ride Reservation Service",
    description="Service for managing ride reservations",
    version="1.0.0",
    root_path="/reservations"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@app.on_event("startup")
async def startup_event():
    # Redis 연결 설정
    app.state.redis = await aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Redis PubSub 설정
    app.state.pubsub = app.state.redis.pubsub()
    
    # 데이터베이스 연결 설정
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    # Redis 연결 종료
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()
    
    # 데이터베이스 연결 종료
    await Database.close_db()

@app.get("/health")
async def health_check():
    """서비스 헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "redis": "connected" if hasattr(app.state, 'redis') else "disconnected"
    }

app.include_router(ride_reservation_router, prefix="/api")
