import json
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_reservation_message(data: Dict[str, Any], redis):
    """예약 메시지 처리"""
    try:
        if data["action"] == "create":
            queue_key = f"ride_queue:{data['ride_id']}"
            rider_status_key = f"rider_status:{data['ride_id']}"
            info_key = f"ride_info:{data['ride_id']}"
            
            logger.info(f"Adding user {data['user_id']} to queue {queue_key}")
            
            # 파이프라인으로 여러 작업 한번에 처리
            pipe = redis.pipeline()
            
            # 대기열에 사용자 추가
            pipe.zadd(queue_key, {data['user_id']: data.get('timestamp', 0)})
            # 사용자 상태를 'queued'로 설정
            pipe.hset(rider_status_key, data['user_id'], "queued")
            
            # 대기열 정보 업데이트
            pipe.hincrby(info_key, "current_queue_length", 1)
            pipe.hincrby(info_key, "total_queue_count", data['number_of_people'])
            
            # 현재 대기자 수 업데이트
            pipe.hget(info_key, "current_waiting_riders")
            pipe.hget(info_key, "current_active_riders")
            pipe.hget(info_key, "total_queue_count")
            
            results = await pipe.execute()
            current_waiting = int(results[-3] or 0)
            current_active = int(results[-2] or 0)
            total_queue_count = int(results[-1] or 0)
            
            logger.info(f"Current status for ride {data['ride_id']}: "
                       f"waiting={current_waiting}, active={current_active}, "
                       f"total_people={total_queue_count}")
            
            # 대기열 위치 확인
            position = await redis.zrank(queue_key, data['user_id'])
            logger.info(f"User {data['user_id']} added to queue at position {position + 1}")
            
        elif data["action"] == "cancel":
            queue_key = f"ride_queue:{data['ride_id']}"
            rider_status_key = f"rider_status:{data['ride_id']}"
            info_key = f"ride_info:{data['ride_id']}"
            waiting_riders_key = f"waiting_riders:{data['ride_id']}"
            active_riders_key = f"active_riders:{data['ride_id']}"
            
            logger.info(f"Processing cancellation for user {data['user_id']} in {queue_key}")
            
            # 현재 사용자 상태 확인
            current_status = await redis.hget(rider_status_key, data['user_id'])
            
            if current_status:
                pipe = redis.pipeline()
                
                # 예약 정보 조회
                reservation_key = f"reservation:{data['user_id']}:{data['ride_id']}"
                reservation_data = await redis.hgetall(reservation_key)
                number_of_people = int(reservation_data.get('number_of_people', 1))
                
                # 상태에 따른 처리
                if current_status == "queued":
                    pipe.zrem(queue_key, data['user_id'])
                    pipe.hincrby(info_key, "current_queue_length", -1)
                    pipe.hincrby(info_key, "total_queue_count", -number_of_people)
                elif current_status == "waiting":
                    pipe.srem(waiting_riders_key, data['user_id'])
                    pipe.hincrby(info_key, "current_waiting_riders", -1)
                elif current_status == "riding":
                    pipe.srem(active_riders_key, data['user_id'])
                    pipe.hincrby(info_key, "current_active_riders", -1)
                
                # 사용자 상태 제거
                pipe.hdel(rider_status_key, data['user_id'])
                
                # 현재 상태 조회
                pipe.hget(info_key, "current_waiting_riders")
                pipe.hget(info_key, "current_active_riders")
                
                results = await pipe.execute()
                current_waiting = int(results[-2] or 0)
                current_active = int(results[-1] or 0)
                
                logger.info(f"User {data['user_id']} removed from {current_status} status")
                logger.info(f"Current status for ride {data['ride_id']}: "
                          f"waiting={current_waiting}, active={current_active}")
            else:
                logger.warning(f"User {data['user_id']} not found in any status")
                
    except Exception as e:
        logger.error(f"Error handling reservation message: {str(e)}")
        logger.exception("Detailed error:")

async def start_pubsub_listener(redis):
    logger.info("Starting Redis PubSub listener")
    pubsub = redis.pubsub()
    
    # 구독할 채널들
    channels = ['ride_reservations', 'ride_cancellations']
    await pubsub.subscribe(*channels)
    logger.info(f"Subscribed to channels: {channels}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                try:
                    logger.debug(f"Received message on channel {message['channel']}: {message['data']}")
                    data = json.loads(message['data'])
                    channel = message['channel']
                    
                    if channel in ['ride_reservations', 'ride_cancellations']:
                        logger.info(f"Processing {channel} message for ride {data.get('ride_id')}")
                        await handle_reservation_message(data, redis)
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message: {message['data']}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    logger.exception("Detailed error:")
                    
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"PubSub listener error: {str(e)}")
        logger.exception("Detailed error:")
    finally:
        logger.info("Unsubscribing from channels")
        await pubsub.unsubscribe()