from .rabbitmq import RabbitMQClient
import os

class EventPublisher:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.client = RabbitMQClient(self.rabbitmq_url)

    async def connect(self):
        await self.client.connect()

    async def publish_structure_update(self, data: dict):
        await self.client.publish('facility.updates', data)

    async def close(self):
        await self.client.close() 