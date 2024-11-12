from fastapi import FastAPI, HTTPException
import os
import aioredis
import logging
from .routes import router
from .redis_pubsub import start_pubsub_listener
import asyncio
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Redis Service",
    description="Service for managing redis queues",
    version="1.0.0",
    root_path="/redis"
)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            
            # 기존 큐 초기화
            for facility in facilities:
                facility_id = str(facility.get("_id"))
                pattern = f"*:{facility_id}"
                
                async for key in redis.scan_iter(match=pattern):
                    await redis.delete(key)
                logging.info(f"Cleared existing keys for facility {facility_id}")
            
            # 새로운 큐 설정
            for facility in facilities:
                facility_id = str(facility.get("_id"))
                
                # 필요한 키들
                queue_key = f"ride_queue:{facility_id}"
                active_riders_key = f"active_riders:{facility_id}"
                
                # 빈 Sorted Set으로 대기열 초기화
                await redis.zadd(queue_key, {f"init:{facility_id}": 0})
                await redis.zrem(queue_key, f"init:{facility_id}")  # 초기화용 더미 데이터 제거
                
                # 빈 Set으로 active_riders 초기화
                await redis.sadd(active_riders_key, "")
                await redis.srem(active_riders_key, "")  # 초기화용 더미 데이터 제거
                
                # 시설 정보 저장
                info_key = f"ride_info:{facility_id}"
                await redis.hmset(info_key, {
                    "facility_name": facility.get("name", "Unknown"),
                    "max_capacity": facility.get("max_queue_capacity", 100),
                    "ride_duration": facility.get("ride_duration", 5),
                    "capacity_per_ride": facility.get("capacity_per_ride", 10),
                    "status": facility.get("status", "active"),
                    "current_waiting_riders": "0",
                    "current_active_riders": "0"
                })
                
                # 라이더 상태 추적을 위한 해시
                rider_status_key = f"rider_status:{facility_id}"
                await redis.hset(rider_status_key, "initialized", "true")
                
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
        
        # PubSub 리스너 시작
        asyncio.create_task(start_pubsub_listener(app.state.redis))
        logging.info("Redis PubSub listener started")
        
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

