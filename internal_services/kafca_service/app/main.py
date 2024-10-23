from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer
import json
import asyncio
import os

app = FastAPI()

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.post("/publish/{topic}")
async def publish_message(topic: str, message: dict):
    try:
        future = producer.send(topic, message)
        result = future.get(timeout=60)
        return {"status": "success", "topic": topic, "offset": result.offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def consume_messages():
    consumer = KafkaConsumer(
        'ride_reservations', 'notifications', 'real_time_updates', 'exit_park', 'facility_queue',
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        if message.topic == 'facility_queue':
            await process_facility_queue(message.value)
        elif message.topic == 'ride_reservations':
            await process_ride_reservation(message.value)
        elif message.topic == 'notifications':
            await process_notification(message.value)
        elif message.topic == 'real_time_updates':
            await process_real_time_update(message.value)
        elif message.topic == 'exit_park':
            await process_exit_park(message.value)

async def process_facility_queue(data):
    facility_id = data['facility_id']
    user_id = data['user_id']
    print(f"User {user_id} added to facility {facility_id} queue.")

async def process_ride_reservation(data):
    # 놀이기구 예약 처리 로직
    print(f"Processing ride reservation: {data}")

async def process_notification(data):
    # 알림 처리 로직
    print(f"Processing notification: {data}")

async def process_real_time_update(data):
    # 실시간 업데이트 처리 로직
    print(f"Processing real-time update: {data}")

async def process_exit_park(data):
    # 공원 퇴장 처리 로직
    print(f"Processing park exit: {data}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages())
