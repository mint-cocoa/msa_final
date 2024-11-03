import aio_pika
import json
from datetime import datetime
from typing import Optional, Dict, Any

class RabbitMQPublisher:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel = None

    async def get_channel(self) -> aio_pika.Channel:
        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
        return self.channel

    async def publish_message(self, routing_key: str, message: Dict[str, Any]):
        channel = await self.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routing_key
        )

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()