import aio_pika
import json
from typing import Optional

class RabbitMQPublisher:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel = None

    async def get_channel(self) -> aio_pika.Channel:
        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
        return self.channel

    async def publish_facility_event(
        self,
        action: str,
        facility_id: str,
        name: Optional[str] = None,
        parent_id: Optional[str] = None
    ):
        message = {
            "action": action,
            "node_type": "facility",
            "reference_id": facility_id
        }
        
        if name:
            message["name"] = name
        if parent_id:
            message["parent_id"] = parent_id

        channel = await self.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key='structure_updates'
        )

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close() 