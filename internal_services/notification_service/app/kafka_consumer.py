from kafka import KafkaConsumer
import json
import os
from .operations import process_notification

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")

def start_kafka_consumer():
    consumer = KafkaConsumer(
        'ride_reservations',
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        process_notification(message.value)
