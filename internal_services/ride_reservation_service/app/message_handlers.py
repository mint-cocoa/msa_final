from datetime import datetime
from .database import get_redis

class ReservationMessageHandler:
    def __init__(self, redis_publisher):
        self.redis_publisher = redis_publisher

    async def handle_reservation_create(self, user_id: str, ride_id: str, 
                                     number_of_people: int, reservation_time: datetime):
        redis = await get_redis()
        
        # Redis에 예약 정보 저장
        reservation_key = f"reservation:{user_id}:{ride_id}"
        reservation_data = {
            "user_id": user_id,
            "ride_id": ride_id,
            "number_of_people": number_of_people,
            "reservation_time": reservation_time.isoformat(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await redis.hmset(reservation_key, reservation_data)
        
        # 대기열에 추가
        queue_key = f"ride_queue:{ride_id}"
        score = int(reservation_time.timestamp())
        await redis.zadd(queue_key, {user_id: score})
        
        position = await redis.zrank(queue_key, user_id)
        
        # Redis Pub/Sub을 통해 예약 생성 이벤트 발행
        message = {
            "action": "create",
            "user_id": user_id,
            "ride_id": ride_id,
            "position": position + 1,
            "number_of_people": number_of_people,
            "reservation_time": reservation_time.isoformat()
        }
        await self.redis_publisher.publish_message('ride_reservations', message)
        
        return position + 1

    async def handle_reservation_cancel(self, user_id: str, ride_id: str, reason: str = None):
        redis = await get_redis()
        
        reservation_key = f"reservation:{user_id}:{ride_id}"
        reservation = await redis.hgetall(reservation_key)
        
        if not reservation:
            return False
            
        queue_key = f"ride_queue:{ride_id}"
        await redis.zrem(queue_key, user_id)
        
        await redis.hset(reservation_key, mapping={
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancel_reason": reason or ""
        })
        
        message = {
            "action": "cancel",
            "user_id": user_id,
            "ride_id": ride_id,
            "reason": reason
        }
        await self.redis_publisher.publish_message('ride_cancellations', message)
        
        return True