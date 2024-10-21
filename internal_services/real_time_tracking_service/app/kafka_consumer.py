from common.config import get_kafka_consumer
from .operations import process_tracking_update

async def start_kafka_consumer():
    consumer = get_kafka_consumer()
    for message in consumer:
        if message.value.get("service") == "real_time_tracking":
            await process_tracking_update(message.value.get("payload"))
