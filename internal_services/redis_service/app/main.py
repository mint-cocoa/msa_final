from fastapi import FastAPI, HTTPException
import os
import aioredis
import httpx
import logging
from .routes import router
from prometheus_fastapi_instrumentator import Instrumentator
from .metrics import *
import asyncio

app = FastAPI(
    title="Redis Service",
    description="Service for managing redis queues",
    version="1.0.0",
    root_path="/redis"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
FACILITY_SERVICE_URL = os.getenv("FACILITY_SERVICE_URL", "http://facility-service:8000")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def initialize_facility_queues(redis):
    """Initialize facility queues by fetching operational facilities from the Facility Service"""
    try:
        async with httpx.AsyncClient() as client:
            logging.info(f"Fetching active facilities from {FACILITY_SERVICE_URL}")
            response = await client.get(f"{FACILITY_SERVICE_URL}/api/facilities/active")
               
            if response.status_code != 200:
                logging.error(f"Failed to get active facilities: {response.text}")
                return
                
            facilities_data = response.json()
            facilities = facilities_data.get("data", {}).get("facilities", [])
            
            logging.info(f"Initializing queues for {len(facilities)} active facilities")
            
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
                
                logging.info(f"Initialized facility {facility_id} with name {facility.get('name')}")
                
    except Exception as e:
        logging.error(f"Failed to initialize facility queues: {str(e)}")
        logging.exception("Detailed error:")

async def check_redis_connection(redis):
    """Redis 연결 상태 확인"""
    try:
        await redis.ping()
        return True
    except Exception as e:
        logging.error(f"Redis connection check failed: {str(e)}")
        return False

@app.on_event("startup")
async def startup_event():
    Instrumentator().instrument(app).expose(app)
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
            
        logging.info("Successfully connected to Redis")
        
        # 시설 대기열 초기화
        await initialize_facility_queues(app.state.redis)
        logging.info("Facility queues initialization completed")
        
        # 메트릭 업데이트 함수
        await update_metrics(app.state.redis)
        
    except Exception as e:
        logging.error(f"Startup failed: {str(e)}")
        logging.exception("Detailed startup error:")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        if hasattr(app.state, "redis"):
            await app.state.redis.close()
            logging.info("Redis connection closed")
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")

@app.get("/health")
async def health_check():
    """서비스 헬스 체크 엔드포인트"""
    if not await check_redis_connection(app.state.redis):
        raise HTTPException(status_code=503, detail="Redis connection failed")
    return {"status": "healthy", "redis": "connected"}

app.include_router(router, prefix="/api")

# 메트릭 업데이트 함수
async def update_metrics(redis):
    while True:
        try:
            # 모든 시설의 큐 상태 조회
            async for key in redis.scan_iter(match="ride_queue:*"):
                facility_id = key.split(":")[1]
                info_key = f"ride_info:{facility_id}"
                
                # 시설 정보 조회
                facility_info = await redis.hgetall(info_key)
                facility_name = facility_info.get('facility_name', 'Unknown')
                
                # 큐 길이
                queue_length = await redis.zcard(key)
                QUEUE_LENGTH.labels(
                    facility_id=facility_id,
                    facility_name=facility_name
                ).set(queue_length)
                
                # 대기 시간 계산
                capacity_per_ride = int(facility_info.get('capacity_per_ride', 1))
                ride_duration = int(facility_info.get('ride_duration', 5))
                wait_time = (queue_length / capacity_per_ride) * ride_duration
                WAITING_TIME.labels(
                    facility_id=facility_id,
                    facility_name=facility_name
                ).set(wait_time)
                
                # 활성 탑승객
                active_riders_key = f"active_riders:{facility_id}"
                active_count = await redis.scard(active_riders_key)
                ACTIVE_RIDERS.labels(
                    facility_id=facility_id,
                    facility_name=facility_name
                ).set(active_count)
                
                # 큐 용량
                max_capacity = int(facility_info.get('max_capacity', 100))
                QUEUE_CAPACITY.labels(
                    facility_id=facility_id,
                    facility_name=facility_name
                ).set(max_capacity)
                
        except Exception as e:
            logging.error(f"Error updating metrics: {e}")
            
        await asyncio.sleep(15)  # 15초마다 업데이트
