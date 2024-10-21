from common.config import redis_client

async def process_tracking_update(data):
    # 실시간 추적 업데이트 처리 로직
    user_id = data.get("user_id")
    location = data.get("location")
    
    # Redis에 위치 정보 업데이트
    await redis_client.geoadd("user_locations", location["longitude"], location["latitude"], user_id)
    
    print(f"Updated location for user {user_id}: {location}")
