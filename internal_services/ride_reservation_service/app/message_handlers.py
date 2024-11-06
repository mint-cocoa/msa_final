from datetime import datetime
from .database import get_redis
import json

class ReservationMessageHandler:
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
        
        # Redis PubSub을 통해 예약 생성 이벤트 발행
        message = {
            "action": "create",
            "user_id": user_id,
            "ride_id": ride_id,
            "number_of_people": number_of_people,
            "timestamp": int(reservation_time.timestamp()),
            "reservation_time": reservation_time.isoformat()
        }
        await redis.publish('ride_reservations', json.dumps(message))
        
        # 대기열 위치 확인
        queue_key = f"ride_queue:{ride_id}"
        position = await redis.zrank(queue_key, user_id)
        return position + 1 if position is not None else None

    async def handle_reservation_cancel(self, user_id: str, ride_id: str, reason: str = None):
        redis = await get_redis()
        
        reservation_key = f"reservation:{user_id}:{ride_id}"
        reservation = await redis.hgetall(reservation_key)
        
        if not reservation:
            return False
            
        # Redis PubSub을 통해 취소 이벤트 발행
        message = {
            "action": "cancel",
            "user_id": user_id,
            "ride_id": ride_id,
            "reason": reason
        }
        await redis.publish('ride_cancellations', json.dumps(message))
        
        # 예약 상태 업데이트
        await redis.hset(reservation_key, mapping={
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancel_reason": reason or ""
        })
        
        return True