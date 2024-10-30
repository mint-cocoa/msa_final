import httpx
from .database import redis_client
import time
from datetime import datetime
import json

async def process_reservation(data):
    # 예약 처리 로직
    reservation_id = data.get("reservation_id")
    user_id = data.get("user_id")
    ride_id = data.get("ride_id")
    
    # Redis에 예약 정보 저장
    await redis_client.hset(f"reservation:{reservation_id}", mapping={
        "user_id": user_id,
        "ride_id": ride_id,
        "status": "confirmed"
    })
    
    # 예약 큐에 추가
    await redis_client.zadd(f"ride_queue:{ride_id}", {user_id: int(data.get("timestamp", 0))})

    print(f"Reservation {reservation_id} processed for user {user_id} on ride {ride_id}")

async def update_operating_facilities():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://facility-service/facilities/operating")
        if response.status_code == 200:
            operating_facilities = response.json()
            
            # 현재 Redis에 있는 모든 ride_queue 키 가져오기
            existing_queues = await redis_client.keys("ride_queue:*")
            existing_ride_ids = set(queue.split(":")[1] for queue in existing_queues)
            
            for facility in operating_facilities:
                ride_id = str(facility["id"])
                if ride_id not in existing_ride_ids:
                    # 새로 운 시작된 기구에 대한 큐 생성
                    await redis_client.zadd(f"ride_queue:{ride_id}", {})
                existing_ride_ids.discard(ride_id)
            
            # 운영 종료된 기구의 큐 삭제
            for ride_id in existing_ride_ids:
                await redis_client.delete(f"ride_queue:{ride_id}")
        
        else:
            print(f"시설 정보를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")

async def get_reservation(reservation_id: str):
    redis = await redis_client.get_redis_client()
    reservation = await redis.hgetall(f"reservation:{reservation_id}")
    if not reservation:
        return None
    return reservation

async def add_to_queue(redis, ride_id: str, user_id: str, number_of_people: int, reservation_time: datetime):
    queue_key = f"ride_queue:{ride_id}"
    reservation_data = {
        "user_id": user_id,
        "number_of_people": number_of_people,
        "reservation_time": reservation_time.isoformat(),
        "timestamp": time.time()
    }
    
    # 예약 시간별로 정렬된 집합에 추가
    score = int(reservation_time.timestamp())
    await redis.zadd(queue_key, {json.dumps(reservation_data): score})
    
    # 현재 대기 인원 수 업데이트
    await redis.hincrby(f"ride_stats:{ride_id}", "waiting_people", number_of_people)
    
    position = await redis.zrank(queue_key, json.dumps(reservation_data))
    return position + 1

async def get_queue_position(redis, ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    queue_data = await redis.zrange(queue_key, 0, -1, withscores=True)
    
    for idx, (data, _) in enumerate(queue_data):
        reservation = json.loads(data)
        if reservation["user_id"] == user_id:
            return idx + 1
    return None

async def cancel_reservation(redis, ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    queue_data = await redis.zrange(queue_key, 0, -1, withscores=True)
    
    for data, score in queue_data:
        reservation = json.loads(data)
        if reservation["user_id"] == user_id:
            # 예약 삭제
            await redis.zrem(queue_key, data)
            # 대기 인원 수 감소
            await redis.hincrby(f"ride_stats:{ride_id}", "waiting_people", -reservation["number_of_people"])
            return True
    return False

async def get_ride_stats(redis, ride_id: str):
    stats_key = f"ride_stats:{ride_id}"
    stats = await redis.hgetall(stats_key)
    return {
        "waiting_people": int(stats.get("waiting_people", 0)),
        "total_reservations": await redis.zcard(f"ride_queue:{ride_id}")
    }
