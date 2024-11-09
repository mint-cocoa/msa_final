from fastapi import FastAPI, HTTPException
import os
import aioredis
import httpx
import logging
from .routes import router
app = FastAPI(
    title="Redis Service",
    description="Service for managing redis queues",
    version="1.0.0",
    root_path="/redis"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
FACILITY_SERVICE_URL = os.getenv("FACILITY_SERVICE_URL", "http://facility-service:8000")

logger = logging.getLogger(__name__)

async def initialize_facility_queues(redis):
    """Initialize facility queues by fetching operational facilities from the Facility Service"""
    try:
        async with httpx.AsyncClient() as client:
            # Fetch active facilities
            response = await client.get(f"{FACILITY_SERVICE_URL}/api/facilities/active")
            if response.status_code != 200:
                logger.error(f"Failed to get active facilities: {response.text}")
                return
                
            facilities_data = response.json()
            facilities = facilities_data.get("data", {}).get("facilities", [])
            
            logger.info(f"Initializing queues for {len(facilities)} active facilities")
            
            for facility in facilities:
                facility_id = str(facility.get("_id"))
                
                # 대기열 관련 키들
                queue_key = f"ride_queue:{facility_id}"
                active_riders_key = f"active_riders:{facility_id}"
                waiting_riders_key = f"waiting_riders:{facility_id}"
                
                # 기존 큐들 초기화
                await redis.delete(queue_key)
                await redis.delete(active_riders_key)
                await redis.delete(waiting_riders_key)
                
                # 시설 정보 저장
                info_key = f"ride_info:{facility_id}"
                await redis.hmset(info_key, {
                    "facility_name": facility.get("name", "Unknown"),
                    "max_capacity": facility.get("max_queue_capacity", 100),
                    "ride_duration": facility.get("ride_duration", 5),
                    "capacity_per_ride": facility.get("capacity_per_ride", 10),
                    "status": facility.get("status", "active"),
                })
                
                # 라이더 상태 추적을 위한 해시 생성
                rider_status_key = f"rider_status:{facility_id}"
                await redis.delete(rider_status_key)
                
                logger.info(f"Initialized facility {facility_id} with name {facility.get('name')}")
                
    except Exception as e:
        logger.error(f"Failed to initialize facility queues: {str(e)}")
        logger.exception("Detailed error:")

async def check_redis_connection(redis):
    """Redis 연결 상태 확인"""
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return False

@app.on_event("startup")
async def startup_event():
    try:
        # Redis 클라이언트 초기화
        app.state.redis = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Redis 연결 확인
        if not await check_redis_connection(app.state.redis):
            raise Exception("Failed to connect to Redis")
            
        logger.info("Successfully connected to Redis")
        
        # 시설 대기열 초기화
        await initialize_facility_queues(app.state.redis)
        logger.info("Facility queues initialization completed")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        logger.exception("Detailed startup error:")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        if hasattr(app.state, "redis"):
            await app.state.redis.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/health")
async def health_check():
    """서비스 헬스 체크 엔드포인트"""
    if not await check_redis_connection(app.state.redis):
        raise HTTPException(status_code=503, detail="Redis connection failed")
    return {"status": "healthy", "redis": "connected"}

app.include_router(router, prefix="/api")
