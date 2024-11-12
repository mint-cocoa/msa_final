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
            pipe.hincrby(info_key, "current_waiting_riders", 1)
            
            # 현재 상태 조회
            pipe.hget(info_key, "current_waiting_riders")
            pipe.hget(info_key, "current_active_riders")
            
            results = await pipe.execute()
            current_waiting = int(results[-2] or 0)
            current_active = int(results[-1] or 0)
            
            logger.info(f"Current status for ride {data['ride_id']}: "
                       f"waiting={current_waiting}, active={current_active}")
            
            # 대기열 위치 확인
            position = await redis.zrank(queue_key, data['user_id'])
            logger.info(f"User {data['user_id']} added to queue at position {position + 1}")
            
        elif data["action"] == "cancel":
            queue_key = f"ride_queue:{data['ride_id']}"
            rider_status_key = f"rider_status:{data['ride_id']}"
            info_key = f"ride_info:{data['ride_id']}"
            active_riders_key = f"active_riders:{data['ride_id']}"
            
            logger.info(f"Processing cancellation for user {data['user_id']} in {queue_key}")
            
            # 현재 사용자 상태 확인
            current_status = await redis.hget(rider_status_key, data['user_id'])
            
            if current_status:
                pipe = redis.pipeline()
                
                # 상태에 따른 처리
                if current_status == "queued":
                    pipe.zrem(queue_key, data['user_id'])
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

async def handle_operation_message(data: Dict[str, Any], redis):
    """운영 메시지 처리"""
    try:
        if data["action"] == "start_ride":
            ride_id = data["ride_id"]
            info_key = f"ride_info:{ride_id}"
            facility_info = await redis.hgetall(info_key)
            capacity = int(facility_info.get('capacity_per_ride', 10))
            
            # 대기열에서 다음 탑승자들 선택
            queue_key = f"ride_queue:{ride_id}"
            next_riders = await redis.zrange(queue_key, 0, capacity - 1)
            
            if not next_riders:
                logger.warning(f"No riders in queue for ride {ride_id}")
                return
                
            active_riders_key = f"active_riders:{ride_id}"
            
            # 파이프라인으로 여러 작업 한번에 처리
            pipe = redis.pipeline()
            
            # 대기열에서 제거하고 active로 이동
            pipe.zrem(queue_key, *next_riders)
            pipe.sadd(active_riders_key, *next_riders)
            
            # rider_status 업데이트
            rider_status_key = f"rider_status:{ride_id}"
            for rider in next_riders:
                pipe.hset(rider_status_key, rider, "riding")
            
            # 상태 업데이트
            remaining_in_queue = max(0, await redis.zcard(queue_key) - len(next_riders))
            pipe.hset(info_key, mapping={
                "current_waiting_riders": str(remaining_in_queue),
                "current_active_riders": str(len(next_riders))
            })
            
            await pipe.execute()
            logger.info(f"Started ride for {len(next_riders)} riders in {ride_id}")
            
        elif data["action"] == "complete_ride":
            ride_id = data["ride_id"]
            active_riders_key = f"active_riders:{ride_id}"
            info_key = f"ride_info:{ride_id}"
            queue_key = f"ride_queue:{ride_id}"
            rider_status_key = f"rider_status:{ride_id}"
            
            # 현재 탑승 중인 사용자들 조회
            active_riders = await redis.smembers(active_riders_key)
            
            if not active_riders:
                logger.warning(f"No active riders for ride {ride_id}")
                return
                
            pipe = redis.pipeline()
            
            # 활성 상태에서 제거
            pipe.srem(active_riders_key, *active_riders)
            
            # rider_status 제거
            for rider in active_riders:
                pipe.hdel(rider_status_key, rider)
            
            # 현재 대기열 길이 조회
            current_queue_length = await redis.zcard(queue_key)
            
            # 상태 업데이트
            pipe.hset(info_key, mapping={
                "current_active_riders": "0",
                "current_waiting_riders": str(current_queue_length)
            })
            
            await pipe.execute()
            logger.info(f"Completed ride for {len(active_riders)} riders in {ride_id}")
            
    except Exception as e:
        logger.error(f"Error handling operation message: {str(e)}")
        logger.exception("Detailed error:")

async def handle_status_message(data: Dict[str, Any], redis):
    """상태 조회 메시지 처리"""
    try:
        ride_id = data["ride_id"]
        user_id = data.get("user_id")
        
        # 상태 정보 수집
        info_key = f"ride_info:{ride_id}"
        queue_key = f"ride_queue:{ride_id}"
        rider_status_key = f"rider_status:{ride_id}"
        
        # 파이프라인으로 여러 정보 조회
        pipe = redis.pipeline()
        pipe.hgetall(info_key)
        pipe.zcard(queue_key)
        if user_id:
            pipe.hget(rider_status_key, user_id)
            pipe.zrank(queue_key, user_id)
        
        results = await pipe.execute()
        
        ride_info = results[0]
        queue_length = results[1]
        
        response = {
            "queue_length": queue_length,
            "current_active_riders": int(ride_info.get('current_active_riders', 0)),
            "current_waiting_riders": int(ride_info.get('current_waiting_riders', 0)),
            "max_capacity": int(ride_info.get('max_capacity', 100)),
            "capacity_per_ride": int(ride_info.get('capacity_per_ride', 10)),
            "ride_duration": int(ride_info.get('ride_duration', 5)),
            "status": "available" if queue_length < int(ride_info.get('max_capacity', 100)) else "full"
        }
        
        if user_id:
            user_status = results[2]
            if user_status:
                response["user_status"] = user_status
                if user_status == "queued":
                    position = results[3]
                    if position is not None:
                        response["user_position"] = position + 1
                        capacity_per_ride = int(ride_info.get('capacity_per_ride', 1))
                        ride_duration = int(ride_info.get('ride_duration', 5))
                        response["estimated_wait_time"] = ((position) // capacity_per_ride) * ride_duration
        
        # 응답 전송
        response_channel = f"status_response:{ride_id}:{user_id}"
        await redis.publish(response_channel, json.dumps(response))
        
    except Exception as e:
        logger.error(f"Error handling status message: {str(e)}")
        logger.exception("Detailed error:")

async def start_pubsub_listener(redis):
    logger.info("Starting Redis PubSub listener")
    pubsub = redis.pubsub()
    
    channels = ['ride_reservations', 'ride_cancellations', 'ride_operations', 'ride_status']
    await pubsub.subscribe(*channels)
    logger.info(f"Subscribed to channels: {channels}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                try:
                    data = json.loads(message['data'])
                    channel = message['channel']
                    
                    if channel in ['ride_reservations', 'ride_cancellations']:
                        await handle_reservation_message(data, redis)
                    elif channel == 'ride_operations':
                        await handle_operation_message(data, redis)
                    elif channel == 'ride_status':
                        await handle_status_message(data, redis)
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message: {message['data']}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"PubSub listener error: {str(e)}")
    finally:
        await pubsub.unsubscribe()