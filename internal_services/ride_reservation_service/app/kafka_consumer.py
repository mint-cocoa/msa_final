from common.config import get_kafka_consumer
from .operations import process_reservation

async def start_kafka_consumer():
    consumer = get_kafka_consumer()
    for message in consumer:
        if message.value.get("service") == "ride_reservation":
            await process_reservation(message.value.get("payload"))
