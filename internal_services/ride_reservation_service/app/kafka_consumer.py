from common.config import get_kafka_consumer
from .operations import process_reservation
from kafka import KafkaConsumer
import json
import aioredis
import asyncio

REDIS_URL = "redis://redis:6379"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def process_message(message):
    redis = await get_redis()
    reservation = json.loads(message.value)
    
    # Redis에 예약 정보 저장
    await redis.hset(f"reservation:{reservation['ride_id']}", mapping=reservation)
    await redis.expire(f"reservation:{reservation['ride_id']}", 86400)  # 24시간 후 만료

def start_consumer():
    consumer = KafkaConsumer('ride_reservations',
                             bootstrap_servers=['kafka:9092'],
                             value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    
    for message in consumer:
        asyncio.run(process_message(message))

if __name__ == "__main__":
    start_consumer()
