import aio_pika
import json
from datetime import datetime
from typing import Optional

class RabbitMQPublisher:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel = None

    async def get_channel(self) -> aio_pika.Channel:
        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
        return self.channel

    async def publish_reservation_event(
        self,
        action: str,
        user_id: str,
        ride_id: str,
        position: Optional[int] = None,
        number_of_people: Optional[int] = None,
        reservation_time: Optional[datetime] = None
    ):
        message = {
            "action": action,
            "user_id": user_id,
            "ride_id": ride_id
        }
        
        if position is not None:
            message["position"] = position
        if number_of_people is not None:
            message["number_of_people"] = number_of_people
        if reservation_time is not None:
            message["reservation_time"] = reservation_time.isoformat()

        channel = await self.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key='ride_reservations'
        )

    async def publish_cancellation_event(
        self,
        user_id: str,
        ride_id: str,
        reason: Optional[str] = None
    ):
        message = {
            "action": "cancel",
            "user_id": user_id,
            "ride_id": ride_id
        }
        
        if reason:
            message["reason"] = reason

        channel = await self.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key='ride_cancellations'
        )

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close() 