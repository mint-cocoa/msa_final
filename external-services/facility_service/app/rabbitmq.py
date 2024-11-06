import aio_pika
import json
import logging
from typing import Optional

class RabbitMQClient:
    def __init__(self, url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self.url = url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        if not self.connection:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    "theme_park_events",
                    aio_pika.ExchangeType.TOPIC
                )
                logging.info("Successfully connected to RabbitMQ")
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ: {e}")
                raise

    async def publish(self, routing_key: str, message: dict):
        if not self.exchange:
            await self.connect()
        
        try:
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json"
                ),
                routing_key=routing_key
            )
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None 