import httpx
from .database import redis_client
import time

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

async def add_to_queue(redis, ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    timestamp = time.time()
    await redis.zadd(queue_key, {user_id: timestamp})
    position = await redis.zrank(queue_key, user_id)
    return position + 1  # 1-based indexing

async def get_queue_position(redis, ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    position = await redis.zrank(queue_key, user_id)
    return position + 1 if position is not None else None

async def remove_from_queue(redis, ride_id: str, user_id: str):
    queue_key = f"ride_queue:{ride_id}"
    removed = await redis.zrem(queue_key, user_id)
    return removed > 0
