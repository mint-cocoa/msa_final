from fastapi import APIRouter, HTTPException, Request
import os
import logging
import time
import json

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
    try:
        info_key = f"ride_info:{ride_id}"
        info = await request.app.state.redis.hgetall(info_key)
        
        if not info:
            logger.warning(f"Ride information not found for ride_id: {ride_id}")
            raise HTTPException(status_code=404, detail="Ride information not found")
            
        # 문자열을 정수로 변환
        capacity_per_ride = int(info.get('capacity_per_ride', 1))
        ride_duration = int(info.get('ride_duration', 5))
        queue_length = int(info.get('current_waiting_riders', 0))
        
        # 예상 대기 시간 계산
        estimated_wait_time = (queue_length / capacity_per_ride) * ride_duration
        
        # 딕셔너리에 새로운 키-값 추가
        info['estimated_wait_time'] = str(estimated_wait_time)
        
        logger.info(f"Retrieved ride info for {ride_id} with wait time: {estimated_wait_time}")
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ride info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ride info: {str(e)}")

@router.get("/queues/summary")
async def get_queues_summary(request: Request):
    """모든 시설의 대기열 요약 정보 조회"""
    try:
        logger.info("시설 대기열 요약 정보 조회 시작")
        summary = []
        
        # Redis에서 모든 ride_queue 키 조회
        queue_keys = []
        async for key in request.app.state.redis.scan_iter(match="ride_queue:*"):
            queue_keys.append(key)
        
        logger.info(f"발견된 대기열 키: {queue_keys}")
        
        for key in queue_keys:
            facility_id = key.split(":")[1]
            logger.info(f"시설 ID {facility_id} 처리 중")
            
            # 대기열 길이
            queue_length = await request.app.state.redis.zcard(key)
            logger.info(f"대기열 길이: {queue_length}")
            
            # 시설 정보
            info_key = f"ride_info:{facility_id}"
            facility_info = await request.app.state.redis.hgetall(info_key)
            logger.info(f"시설 정보: {facility_info}")
            
            if not facility_info:
                logger.warning(f"시설 정보를 찾을 수 없음: {facility_id}")
                continue
            
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
        
        logger.info(f"처리된 총 시설 수: {len(summary)}")
        return {
            "total_facilities": len(summary),
            "queues_summary": summary
        }
        
    except Exception as e:
        logger.error(f"대기열 요약 정보 조회 중 오류 발생: {str(e)}")
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
    """대기열에서 active로 이동"""
    try:
        # Redis PubSub으로 메시지 발행
        message = {
            "action": "start_ride",
            "ride_id": ride_id,
            "timestamp": time.time()
        }
        
        await request.app.state.redis.publish('ride_operations', json.dumps(message))
        logger.info(f"Published start_ride message for ride {ride_id}")
        
        return {
            "status": "processing",
            "message": f"Start ride request for {ride_id} has been queued"
        }
    except Exception as e:
        logger.error(f"Error publishing start ride message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/riders/complete-ride/{ride_id}")
async def complete_ride(ride_id: str, request: Request):
    """탑승 완료 처리"""
    try:
        # Redis PubSub으로 메시지 발행
        message = {
            "action": "complete_ride",
            "ride_id": ride_id,
            "timestamp": time.time()
        }
        
        await request.app.state.redis.publish('ride_operations', json.dumps(message))
        logger.info(f"Published complete_ride message for ride {ride_id}")
        
        return {
            "status": "processing",
            "message": f"Complete ride request for {ride_id} has been queued"
        }
    except Exception as e:
        logger.error(f"Error publishing complete ride message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/facility/reset/{facility_id}")
async def reset_facility_queue(facility_id: str, request: Request):
    """특정 시설의 모든 큐를 초기화"""
    try:
        # 시설 정보 조회
        info_key = f"ride_info:{facility_id}"
        facility_info = await request.app.state.redis.hgetall(info_key)
        
        if not facility_info:
            raise HTTPException(status_code=404, detail="Facility not found")
            
        # 초기화할 큐 키들
        queue_key = f"ride_queue:{facility_id}"
        active_riders_key = f"active_riders:{facility_id}"
        waiting_riders_key = f"waiting_riders:{facility_id}"
        rider_status_key = f"rider_status:{facility_id}"
        
        pipe = request.app.state.redis.pipeline()
        
        # 모든 큐 초기화
        pipe.delete(queue_key)
        pipe.delete(active_riders_key)
        pipe.delete(waiting_riders_key)
        pipe.delete(rider_status_key)
        
        # 빈 큐들 다시 생성
        pipe.zadd(queue_key, {f"init:{facility_id}": 0})  # 빈 대기열 초기화
        pipe.sadd(active_riders_key, "")  # 빈 활성 라이더 세트
        pipe.sadd(waiting_riders_key, "")  # 빈 대기 라이더 세트
        
        # 시설 정보 초기화
        pipe.hset(info_key, mapping={
            "current_queue_length": 0,
            "current_waiting_riders": 0,
            "current_active_riders": 0,
            "total_queue_count": 0,
            "facility_name": facility_info.get("facility_name", "Unknown"),
            "max_capacity": facility_info.get("max_capacity", 100),
            "ride_duration": facility_info.get("ride_duration", 5),
            "capacity_per_ride": facility_info.get("capacity_per_ride", 10),
            "status": facility_info.get("status", "active")
        })
        
        # 라이더 상태 초기화
        pipe.hset(rider_status_key, "initialized", "true")
        
        await pipe.execute()
        
        logger.info(f"Successfully reset all queues for facility {facility_id}")
        return {
            "status": "success",
            "message": f"All queues reset for facility {facility_id}",
            "facility_id": facility_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting facility queues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
