from common.config import redis_client

async def process_notification(data):
    # 알림 처리 로직
    user_id = data.get("user_id")
    message = data.get("message")
    
    # Redis에 알림 저장
    await redis_client.lpush(f"notifications:{user_id}", message)
    
    print(f"Notification sent to user {user_id}: {message}")
