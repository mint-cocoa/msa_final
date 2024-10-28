import aio_pika
import json
import asyncio
import os
import aioredis

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

async def get_redis():
    return await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def process_message(message):
    async with message.process():
        try:
            reservation = json.loads(message.body.decode())
            user_id = reservation["user_id"]
            ride_id = reservation["ride_id"]
            
            redis = await get_redis()
            
            # Redis에 예약 정보 저장
            queue_key = f"ride_queue:{ride_id}"
            await redis.zadd(queue_key, {user_id: 0})  # 우선순위 큐에 사용자 추가
            print(f"Reservation processed: User {user_id} added to ride {ride_id} queue.")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing message: {e}")
        except aioredis.RedisError as e:
            print(f"Redis error: {e}")

async def start_consumer():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    queue = await channel.declare_queue("ride_reservations", durable=True)
    
    await queue.consume(process_message)
    
    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()

async def run_consumer():
    await start_consumer()

if __name__ == "__main__":
    run_consumer()
