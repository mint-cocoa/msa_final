import json
import asyncio
from typing import Dict, Any

async def handle_reservation_message(data: Dict[str, Any], redis):
    """예약 메시지 처리"""
    if data["action"] == "create":
        # 대기열에 사용자 추가
        queue_key = f"ride_queue:{data['ride_id']}"
        await redis.zadd(queue_key, {data['user_id']: data.get('timestamp', 0)})
        
    elif data["action"] == "cancel":
        # 대기열에서 사용자 제거
        queue_key = f"ride_queue:{data['ride_id']}"
        await redis.zrem(queue_key, data['user_id'])

async def start_pubsub_listener(redis):
    pubsub = redis.pubsub()
    
    # 구독할 채널들
    channels = ['ride_reservations', 'ride_cancellations']
    await pubsub.subscribe(*channels)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                try:
                    data = json.loads(message['data'])
                    channel = message['channel']
                    
                    if channel in ['ride_reservations', 'ride_cancellations']:
                        await handle_reservation_message(data, redis)
                        
                except json.JSONDecodeError:
                    print(f"Invalid JSON message: {message['data']}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
            await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe() 