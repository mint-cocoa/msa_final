import os
import aioredis
from kafka import KafkaConsumer
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")
KAFKA_TOPIC = "park_operations"

redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

def get_kafka_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
