from fastapi import APIRouter, HTTPException, Request
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

REDIS_SERVICE_URL = os.getenv("REDIS_SERVICE_URL", "http://redis-service:8000")

@router.get("/queue_position/{ride_id}/{user_id}")
async def get_queue_position(ride_id: str, user_id: str, request: Request):
    logger.info(f"Checking queue position for user {user_id} in ride {ride_id}")
    try:
        queue_key = f"ride_queue:{ride_id}"
        position = await request.app.state.redis.zrank(queue_key, user_id)
        if position is None:
            logger.warning(f"User {user_id} not found in queue {ride_id}")
            raise HTTPException(status_code=404, detail="User not in queue")
        logger.info(f"User {user_id} is at position {position + 1} in queue {ride_id}")
        return {"position": position + 1}
    except Exception as e:
        logger.error(f"Error getting queue position: {str(e)}")
        raise

@router.post("/dequeue/front/{ride_id}/{count}")
async def dequeue_users(ride_id: str, count: int, request: Request):
    logger.info(f"Attempting to dequeue {count} users from ride {ride_id}")
    try:
        queue_key = f"ride_queue:{ride_id}"
        user_ids = await request.app.state.redis.zrange(queue_key, 0, count - 1)
        
        if not user_ids:
            logger.warning(f"No users to dequeue from ride {ride_id}")
            raise HTTPException(status_code=404, detail="Queue is empty or not enough users")
        
        for user_id in user_ids:
            await request.app.state.redis.zrem(queue_key, user_id)
            logger.info(f"Dequeued user {user_id} from ride {ride_id}")
        
        logger.info(f"Successfully dequeued {len(user_ids)} users from ride {ride_id}")
        return {"message": f"{len(user_ids)} users removed from queue for ride {ride_id}"}
    except Exception as e:
        logger.error(f"Error dequeuing users: {str(e)}")
        raise

@router.get("/queues/all")
async def get_all_queues_status(request: Request):
    logger.info("Fetching status for all queues")
    try:
        queue_keys = []
        async for key in request.app.state.redis.scan_iter(match="ride_queue:*"):
            queue_keys.append(key)
        
        logger.info(f"Found {len(queue_keys)} active queues")
        queues_status = {}
        
        for queue_key in queue_keys:
            facility_id = queue_key.split(":")[1]
            logger.debug(f"Processing queue for facility {facility_id}")
            
            queue_length = await request.app.state.redis.zcard(queue_key)
            users = await request.app.state.redis.zrange(queue_key, 0, -1, withscores=True)
            info_key = f"ride_info:{facility_id}"
            facility_info = await request.app.state.redis.hgetall(info_key)
            
            queues_status[facility_id] = {
                "queue_length": queue_length,
                "users": [{"user_id": user[0], "timestamp": user[1]} for user in users],
                "facility_info": facility_info
            }
            
        logger.info("Successfully retrieved all queue statuses")
        return {
            "total_facilities": len(queues_status),
            "queues": queues_status
        }
        
    except Exception as e:
        logger.error(f"Error getting all queues status: {str(e)}")
        logger.exception("Detailed error:")
        raise HTTPException(status_code=500, detail=f"Failed to get queues status: {str(e)}")

@router.get("/queue_status/{ride_id}")
async def get_queue_status(ride_id: str, request: Request):
    queue_key = f"ride_queue:{ride_id}"
    user_ids = await request.app.state.redis.zrange(queue_key, 0, -1)
    if not user_ids:
        raise HTTPException(status_code=404, detail="Queue is empty")
    return {"user_ids": user_ids}

@router.get("/ride_info/{ride_id}")
async def get_ride_info(ride_id: str, request: Request):
    """시설의 대기열 정보 조회"""
    info_key = f"ride_info:{ride_id}"
    info = await request.app.state.redis.hgetall(info_key)
    if not info:
        raise HTTPException(status_code=404, detail="Ride information not found")
    return info

@router.get("/queues/summary")
async def get_queues_summary(request: Request):
    """모든 시설의 대기열 요약 정보 조회"""
    try:
        summary = []
        async for key in request.app.state.redis.scan_iter(match="ride_queue:*"):
            facility_id = key.split(":")[1]
            
            # 대기열 길이
            queue_length = await request.app.state.redis.zcard(key)
            
            # 시설 정보
            info_key = f"ride_info:{facility_id}"
            facility_info = await request.app.state.redis.hgetall(info_key)
            
            # 예상 대기 시간 계산 (분 단위)
            capacity_per_ride = int(facility_info.get('capacity_per_ride', 1))
            ride_duration = int(facility_info.get('ride_duration', 5))
            estimated_wait_time = (queue_length / capacity_per_ride) * ride_duration
            
            summary.append({
                "facility_id": facility_id,
                "queue_length": queue_length,
                "max_capacity": int(facility_info.get('max_capacity', 100)),
                "estimated_wait_time": estimated_wait_time,
                "status": "full" if queue_length >= int(facility_info.get('max_capacity', 100)) else "available"
            })
        
        return {
            "total_facilities": len(summary),
            "queues_summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queues summary: {str(e)}")

@router.get("/riders/active/{ride_id}")
async def get_active_riders(ride_id: str, request: Request):
    """현재 탑승 중인 사용자 목록 조회"""
    try:
        active_riders_key = f"active_riders:{ride_id}"
        active_riders = await request.app.state.redis.smembers(active_riders_key)
        
        info_key = f"ride_info:{ride_id}"
        facility_info = await request.app.state.redis.hgetall(info_key)
        
        return {
            "ride_id": ride_id,
            "active_riders": list(active_riders),
            "total_active": len(active_riders),
            "capacity_per_ride": int(facility_info.get('capacity_per_ride', 10))
        }
    except Exception as e:
        logger.error(f"Error getting active riders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/riders/waiting/{ride_id}")
async def get_waiting_riders(ride_id: str, request: Request):
    """탑승 대기 중인 사용자 목록 조회"""
    try:
        waiting_riders_key = f"waiting_riders:{ride_id}"
        waiting_riders = await request.app.state.redis.smembers(waiting_riders_key)
        
        return {
            "ride_id": ride_id,
            "waiting_riders": list(waiting_riders),
            "total_waiting": len(waiting_riders)
        }
    except Exception as e:
        logger.error(f"Error getting waiting riders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/riders/start-ride/{ride_id}")
async def start_ride(ride_id: str, request: Request):
    """다음 탑승 시작 - 대기열에서 사용자들을 active로 이동"""
    try:
        info_key = f"ride_info:{ride_id}"
        facility_info = await request.app.state.redis.hgetall(info_key)
        capacity = int(facility_info.get('capacity_per_ride', 10))
        
        # 대기열에서 다음 탑승자들 선택
        queue_key = f"ride_queue:{ride_id}"
        next_riders = await request.app.state.redis.zrange(queue_key, 0, capacity - 1)
        
        if not next_riders:
            raise HTTPException(status_code=404, detail="No riders in queue")
            
        active_riders_key = f"active_riders:{ride_id}"
        waiting_riders_key = f"waiting_riders:{ride_id}"
        
        # 파이프라인으로 여러 작업 한번에 처리
        pipe = request.app.state.redis.pipeline()
        
        # 대기열에서 제거
        pipe.zrem(queue_key, *next_riders)
        # 대기 상태로 이동
        pipe.sadd(waiting_riders_key, *next_riders)
        # 상태 업데이트
        pipe.hset(info_key, "current_waiting_riders", len(next_riders))
        
        await pipe.execute()
        
        logger.info(f"Started ride for {len(next_riders)} riders in {ride_id}")
        return {
            "ride_id": ride_id,
            "started_riders": next_riders,
            "total_started": len(next_riders)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting ride: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/riders/complete-ride/{ride_id}")
async def complete_ride(ride_id: str, request: Request):
    """탑승 완료 처리"""
    try:
        active_riders_key = f"active_riders:{ride_id}"
        waiting_riders_key = f"waiting_riders:{ride_id}"
        info_key = f"ride_info:{ride_id}"
        
        # 현재 탑승 중인 사용자들 조회
        active_riders = await request.app.state.redis.smembers(active_riders_key)
        
        if not active_riders:
            raise HTTPException(status_code=404, detail="No active riders")
            
        # 파이프라인으로 여러 작업 한번에 처리
        pipe = request.app.state.redis.pipeline()
        
        # 활성 상태에서 제거
        pipe.srem(active_riders_key, *active_riders)
        # 상태 업데이트
        pipe.hset(info_key, "current_active_riders", 0)
        
        await pipe.execute()
        
        logger.info(f"Completed ride for {len(active_riders)} riders in {ride_id}")
        return {
            "ride_id": ride_id,
            "completed_riders": list(active_riders),
            "total_completed": len(active_riders)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing ride: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/riders/board/{ride_id}")
async def board_ride(ride_id: str, request: Request):
    """대기 상태에서 탑승 상태로 변경"""
    try:
        waiting_riders_key = f"waiting_riders:{ride_id}"
        active_riders_key = f"active_riders:{ride_id}"
        info_key = f"ride_info:{ride_id}"
        
        # 대기 중인 사용자들 조회
        waiting_riders = await request.app.state.redis.smembers(waiting_riders_key)
        
        if not waiting_riders:
            raise HTTPException(status_code=404, detail="No waiting riders")
            
        # 파이프라인으로 여러 작업 한번에 처리
        pipe = request.app.state.redis.pipeline()
        
        # 대기 상태에서 제거하고 활성 상태로 이동
        pipe.srem(waiting_riders_key, *waiting_riders)
        pipe.sadd(active_riders_key, *waiting_riders)
        
        # 상태 업데이트
        pipe.hset(info_key, "current_waiting_riders", 0)
        pipe.hset(info_key, "current_active_riders", len(waiting_riders))
        
        await pipe.execute()
        
        logger.info(f"Boarded {len(waiting_riders)} riders in {ride_id}")
        return {
            "ride_id": ride_id,
            "boarded_riders": list(waiting_riders),
            "total_boarded": len(waiting_riders)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error boarding ride: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
