import redis.asyncio as redis
import json
import os

class RedisPublisher:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None

    async def connect(self):
        if not self.redis_client:
            self.redis_client = await redis.from_url(self.redis_url)

    async def publish_structure_update(self, data: dict):
        if not self.redis_client:
            await self.connect()
        message = json.dumps(data)
        await self.redis_client.publish('facility_updates', message)

    async def close(self):
        if self.redis_client:
            await self.redis_client.close() 