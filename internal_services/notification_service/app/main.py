from fastapi import FastAPI
from kafka import KafkaConsumer
import json
from .kafka_consumer import start_kafka_consumer
import asyncio
import threading

app = FastAPI()

def send_notification(user_id, message):
    # 실제 알림 전송 로직을 구현합니다 (예: 푸시 알림, 이메일 등)
    print(f"알림 전송: 사용자 {user_id}에게 '{message}' 메시지 전송")

def consume_messages():
    consumer = KafkaConsumer('notifications',
                             bootstrap_servers=['kafka:9092'],
                             value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    for message in consumer:
        notification = message.value
        send_notification(notification['user_id'], notification['message'])

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=start_kafka_consumer, daemon=True).start()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}
