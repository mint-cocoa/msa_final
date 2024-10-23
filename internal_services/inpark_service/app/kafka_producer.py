from aiokafka import AIOKafkaProducer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
QUEUE_TOPIC = "facility_queue"

producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

async def send_queue_request(facility_id: str, user_id: str):
    await producer.start()
    try:
        message = json.dumps({"facility_id": facility_id, "user_id": user_id}).encode('utf-8')
        await producer.send_and_wait(QUEUE_TOPIC, message)
    finally:
        await producer.stop()
