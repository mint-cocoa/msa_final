import aio_pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def publish_structure_update(channel, data: dict, routing_key: str = "structure_updates"):
    message = aio_pika.Message(
        body=json.dumps(data).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    await channel.default_exchange.publish(message, routing_key=routing_key) 