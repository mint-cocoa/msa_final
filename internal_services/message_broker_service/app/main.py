from fastapi import FastAPI, HTTPException, Request
from kafka import KafkaProducer, KafkaConsumer
import json
import asyncio
import os
from typing import Dict, Any

app = FastAPI()

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 서비스별 Kafka 토픽 매핑
SERVICE_TOPICS = {
    "user": "user_service",
    "park": "park_service",
    "facility": "facility_service",
    "ride_reservation": "ride_reservation_service",
    "notification": "notification_service",
    "real_time_tracking": "real_time_tracking_service",
    "inpark": "inpark_service"
}

@app.post("/publish/{service}")
async def publish_message(service: str, request: Request):
    if service not in SERVICE_TOPICS:
        raise HTTPException(status_code=400, detail="Invalid service")
    
    topic = SERVICE_TOPICS[service]
    payload = await request.json()
    
    try:
        # 메시지에 서비스 이름과 원본 페이로드를 포함
        message = {
            "service": service,
            "payload": payload
        }
        future = producer.send(topic, message)
        result = future.get(timeout=60)
        return {"status": "success", "topic": topic, "offset": result.offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def consume_messages():
    consumer = KafkaConsumer(
        *SERVICE_TOPICS.values(),
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        await process_message(message.topic, message.value)

async def process_message(topic: str, message: Dict[str, Any]):
    service = next(key for key, value in SERVICE_TOPICS.items() if value == topic)
    print(f"Processing message for {service}: {message}")
    # 여기에 각 서비스별 처리 로직을 구현합니다.
    # 예를 들어, HTTP 요청을 해당 서비스로 보내거나 다른 처리를 수행할 수 있습니다.

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
