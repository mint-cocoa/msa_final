from datetime import datetime
import json
import logging
from .database import get_redis
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class ReservationMessageHandler:
    async def handle_reservation_create(self, user_id: str, ride_id: str, 
                                     number_of_people: int, reservation_time: datetime):
        try:
            redis = await get_redis()
            
            # 기본 정보 조회만 수행
            info_key = f"ride_info:{ride_id}"
            ride_info = await redis.hgetall(info_key)
            
            if not ride_info:
                logging.error(f"Ride info not found for ride_id: {ride_id}")
                raise ValueError("Invalid ride ID")

            # Redis PubSub을 통해 예약 생성 이벤트 발행
            message = {
                "action": "create",
                "user_id": user_id,
                "ride_id": ride_id,
                "number_of_people": number_of_people,
                "timestamp": int(reservation_time.timestamp())
            }
            
            await redis.publish('ride_reservations', json.dumps(message))
            logging.info(f"Published reservation create event: {message}")
            
            return {
                "status": "queued",
                "message": "Reservation request has been queued",
                "ride_id": ride_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logging.error(f"Error in handle_reservation_create: {str(e)}")
            raise

    async def handle_reservation_cancel(self, user_id: str, ride_id: str, reason: str = None):
        try:
            redis = await get_redis()
            
            # Redis PubSub을 통해 취소 이벤트 발행
            message = {
                "action": "cancel",
                "user_id": user_id,
                "ride_id": ride_id,
                "reason": reason,
                "timestamp": int(datetime.now().timestamp())
            }
            
            await redis.publish('ride_cancellations', json.dumps(message))
            logging.info(f"Published reservation cancel event: {message}")
            
            return {
                "status": "processing",
                "message": "Cancellation request has been queued",
                "ride_id": ride_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logging.error(f"Error in handle_reservation_cancel: {str(e)}")
            raise

    async def get_queue_status(self, ride_id: str, user_id: str = None):
        try:
            redis = await get_redis()
            
            # Redis PubSub을 통해 상태 조회 이벤트 발행
            message = {
                "action": "get_status",
                "ride_id": ride_id,
                "user_id": user_id,
                "timestamp": int(datetime.now().timestamp())
            }
            
            await redis.publish('ride_status', json.dumps(message))
            logging.info(f"Published status check event: {message}")
            
            # 상태 조회는 동기적으로 필요하므로 응답을 기다림
            # 이를 위해 임시 응답 채널 생성
            response_channel = f"status_response:{ride_id}:{user_id}"
            pubsub = redis.pubsub()
            await pubsub.subscribe(response_channel)
            
            try:
                # 응답 대기 (최대 5초)
                for _ in range(50):  # 0.1초 * 50 = 5초
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if message and message['type'] == 'message':
                        return json.loads(message['data'])
                    await asyncio.sleep(0.1)
                
                raise TimeoutError("Status check request timed out")
                
            finally:
                await pubsub.unsubscribe(response_channel)
            
        except Exception as e:
            logging.error(f"Error in get_queue_status: {str(e)}")
            raise