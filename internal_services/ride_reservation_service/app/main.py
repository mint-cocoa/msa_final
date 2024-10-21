from fastapi import FastAPI, HTTPException, Depends
from kafka import KafkaProducer, KafkaConsumer
import json
from .kafka_consumer import start_kafka_consumer
import asyncio
from .dependencies import get_current_user
from .operations import update_operating_facilities
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = FastAPI()

producer = KafkaProducer(bootstrap_servers=['kafka:9092'],
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.post("/reserve/{ride_id}")
async def reserve_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    # 예약 로직 구현
    return {"message": f"Ride {ride_id} reserved for user {user_id}"}

# Kafka 컨슈머 로직 (별도의 스레드에서 실행)
def consume_messages():
    consumer = KafkaConsumer('ride_status',
                             bootstrap_servers=['kafka:9092'],
                             value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    for message in consumer:
        # 여기서 메시지를 처리합니다 (예: 데이터베이스 업데이트)
        print(message.value)

import threading
threading.Thread(target=consume_messages, daemon=True).start()

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_kafka_consumer())
    scheduler.add_job(update_operating_facilities, IntervalTrigger(hours=1))
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
