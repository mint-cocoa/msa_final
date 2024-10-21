from common.config import get_kafka_consumer
from .operations import process_notification

async def start_kafka_consumer():
    consumer = get_kafka_consumer()
    for message in consumer:
        if message.value.get("service") == "notification":
            await process_notification(message.value.get("payload"))
