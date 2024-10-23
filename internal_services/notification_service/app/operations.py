from common.config import redis_client

async def process_notification(data):
    user_id = data.get("user_id")
    ride_id = data.get("ride_id")
    message = f"예약이 완료되었습니다. 사용자: {user_id}, 놀이기구: {ride_id}"
    
    # 실제 알림 전송 로직 구현
    print(f"알림 전송: {message}")
