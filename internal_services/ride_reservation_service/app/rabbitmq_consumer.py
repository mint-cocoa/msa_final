import aio_pika
import json
import aioredis
import asyncio
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

async def get_redis():
    return await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def process_message(message):
    async with message.process():
        redis = await get_redis()
        reservation = json.loads(message.body.decode())
        
        await redis.hset(f"reservation:{reservation['ride_id']}", mapping=reservation)
        await redis.expire(f"reservation:{reservation['ride_id']}", 86400)

async def start_consumer():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    queue = await channel.declare_queue("ride_reservations", durable=True)
    
    await queue.consume(process_message)
    
    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()

def run_consumer():
    asyncio.run(start_consumer())

if __name__ == "__main__":
    run_consumer()
