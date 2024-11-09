from datetime import datetime
import json
import logging
from .database import get_redis

logger = logging.getLogger(__name__)

class ReservationMessageHandler:
    async def handle_reservation_create(self, user_id: str, ride_id: str, 
                                     number_of_people: int, reservation_time: datetime):
        try:
            redis = await get_redis()
            
            # 대기열 용량 확인
            info_key = f"ride_info:{ride_id}"
            ride_info = await redis.hgetall(info_key)
            
            if not ride_info:
                logger.error(f"Ride info not found for ride_id: {ride_id}")
                raise ValueError("Invalid ride ID")
                
            queue_key = f"ride_queue:{ride_id}"
            current_queue_size = await redis.zcard(queue_key)
            max_capacity = int(ride_info.get('max_capacity', 100))
            
            if current_queue_size >= max_capacity:
                logger.warning(f"Queue is full for ride {ride_id}")
                raise ValueError("Queue is full")
            
            # 현재 상태 확인
            rider_status_key = f"rider_status:{ride_id}"
            current_status = await redis.hget(rider_status_key, user_id)
            if current_status in ["waiting", "riding"]:
                raise ValueError(f"User already in {current_status} status")
            
            # 파이프라인으로 여러 작업 한번에 처리
            pipe = redis.pipeline()
            pipe.zadd(queue_key, {user_id: int(reservation_time.timestamp())})
            pipe.hset(rider_status_key, user_id, "queued")
            await pipe.execute()
            
            logger.info(f"Created reservation: {queue_key}")
            
            # Redis PubSub을 통해 예약 생성 이벤트 발행
            message = {
                "action": "create",
                "user_id": user_id,
                "ride_id": ride_id,
                "number_of_people": number_of_people,
                "timestamp": int(reservation_time.timestamp())
            }
            
            await redis.publish('ride_reservations', json.dumps(message))
            logger.info(f"Published reservation create event: {message}")
            
            # 대기열 위치 및 예상 시간 계산
            position = await redis.zrank(queue_key, user_id)
            queue_position = position + 1 if position is not None else None
            
            if queue_position:
                capacity_per_ride = int(ride_info.get('capacity_per_ride', 1))
                ride_duration = int(ride_info.get('ride_duration', 5))
                estimated_wait_time = ((queue_position - 1) // capacity_per_ride) * ride_duration
            else:
                estimated_wait_time = 0
                
            return {
                "position": queue_position,
                "estimated_wait_time": estimated_wait_time,
                "queue_status": "queued",
                "current_status": "queued"
            }
            
        except Exception as e:
            logger.error(f"Error in handle_reservation_create: {str(e)}")
            raise

    async def handle_reservation_cancel(self, user_id: str, ride_id: str, reason: str = None):
        try:
            redis = await get_redis()
            
            # 현재 상태 확인
            rider_status_key = f"rider_status:{ride_id}"
            current_status = await redis.hget(rider_status_key, user_id)
            
            if not current_status:
                logger.warning(f"No status found for user {user_id} in ride {ride_id}")
                return False
            
            # 파이프라인으로 여러 작업 한번에 처리
            pipe = redis.pipeline()
            
            # 상태에 따른 처리
            if current_status == "queued":
                queue_key = f"ride_queue:{ride_id}"
                pipe.zrem(queue_key, user_id)
            elif current_status == "waiting":
                waiting_riders_key = f"waiting_riders:{ride_id}"
                pipe.srem(waiting_riders_key, user_id)
            elif current_status == "riding":
                active_riders_key = f"active_riders:{ride_id}"
                pipe.srem(active_riders_key, user_id)
            
            # 상태 제거
            pipe.hdel(rider_status_key, user_id)
            await pipe.execute()
            
            # Redis PubSub을 통해 취소 이벤트 발행
            message = {
                "action": "cancel",
                "user_id": user_id,
                "ride_id": ride_id,
                "previous_status": current_status,
                "reason": reason
            }
            
            await redis.publish('ride_cancellations', json.dumps(message))
            logger.info(f"Published reservation cancel event: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in handle_reservation_cancel: {str(e)}")
            raise

    async def get_queue_status(self, ride_id: str, user_id: str = None):
        try:
            redis = await get_redis()
            queue_key = f"ride_queue:{ride_id}"
            info_key = f"ride_info:{ride_id}"
            rider_status_key = f"rider_status:{ride_id}"
            
            # 시설 정보 조회
            ride_info = await redis.hgetall(info_key)
            if not ride_info:
                logger.error(f"Ride info not found for ride_id: {ride_id}")
                raise ValueError("Invalid ride ID")
            
            # 대기열 정보 조회
            queue_length = await redis.zcard(queue_key)
            current_active = int(ride_info.get('current_active_riders', 0))
            current_waiting = int(ride_info.get('current_waiting_riders', 0))
            
            response = {
                "queue_length": queue_length,
                "current_active_riders": current_active,
                "current_waiting_riders": current_waiting,
                "max_capacity": int(ride_info.get('max_capacity', 100)),
                "capacity_per_ride": int(ride_info.get('capacity_per_ride', 10)),
                "ride_duration": int(ride_info.get('ride_duration', 5)),
                "status": "available" if queue_length < int(ride_info.get('max_capacity', 100)) else "full"
            }
            
            # 특정 사용자의 정보 조회
            if user_id:
                user_status = await redis.hget(rider_status_key, user_id)
                if user_status:
                    response["user_status"] = user_status
                    
                    if user_status == "queued":
                        position = await redis.zrank(queue_key, user_id)
                        if position is not None:
                            response["user_position"] = position + 1
                            capacity_per_ride = int(ride_info.get('capacity_per_ride', 1))
                            ride_duration = int(ride_info.get('ride_duration', 5))
                            response["estimated_wait_time"] = ((position) // capacity_per_ride) * ride_duration
                    
            return response
            
        except Exception as e:
            logger.error(f"Error in get_queue_status: {str(e)}")
            raise