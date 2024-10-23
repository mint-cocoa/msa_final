from kafka import KafkaProducer
import json
import os

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_message(topic: str, message: dict):
    producer.send(topic, message)
    producer.flush()
