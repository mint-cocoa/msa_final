import redis.asyncio as redis
import json
import asyncio
from .database import get_db
from bson import ObjectId
from datetime import datetime
import httpx
import os

class RedisConsumer:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None
        self.db = None
        self.pubsub = None

    async def connect(self):
        if not self.redis_client:
            self.redis_client = await redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            self.db = await get_db()

    async def subscribe(self):
        await self.pubsub.subscribe(
            "park_create",
            "park_update",
            "park_delete",
            "facility_create",
            "facility_update",
            "facility_delete",
            "ticket_type_create",
            "ticket_type_update",
            "ticket_type_delete"
        )

    async def start_consuming(self):
        await self.connect()
        await self.subscribe()
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    channel = message["channel"].decode()
                    
                    if channel == "park_create":
                        await self.handle_park_event(data)
                    elif channel == "park_update":
                        await self.handle_park_event(data)
                    elif channel == "park_delete":
                        await self.handle_park_event(data)
                    elif channel == "facility_create":
                        await self.handle_facility_event(data)
                    elif channel == "facility_update":
                        await self.handle_facility_event(data)
                    elif channel == "facility_delete":
                        await self.handle_facility_event(data)
                    elif channel == "ticket_type_create":
                        await self.handle_ticket_event(data)
                    elif channel == "ticket_type_update":
                        await self.handle_ticket_event(data)
                    elif channel == "ticket_type_delete":
                        await self.handle_ticket_event(data)    
        except Exception as e:
            print(f"Error in consumer: {e}")

    async def handle_park_event(self, data: dict):
        try:
            if data["action"] == "create":
                await self.db.structure_nodes.insert_one({
                    "node_type": "park",
                    "reference_id": ObjectId(data["reference_id"]),
                    "name": data["name"],
                    "parent_id": None,
                    "created_at": datetime.utcnow()
                })
            elif data["action"] == "update":
                await self.db.structure_nodes.update_one(
                    {"reference_id": ObjectId(data["reference_id"])},
                    {"$set": {"name": data["name"], "updated_at": datetime.utcnow()}}
                )
            elif data["action"] == "delete":
                await self.db.structure_nodes.delete_one(
                    {"reference_id": ObjectId(data["reference_id"])}
                )
        except Exception as e:
            print(f"Error handling park event: {e}")

    async def handle_facility_event(self, data: dict):
        try:
            if data["action"] == "create":
                await self.db.structure_nodes.insert_one({
                    "node_type": "facility",
                    "reference_id": ObjectId(data["reference_id"]),
                    "name": data["name"],
                    "parent_id": ObjectId(data["parent_id"]),
                    "created_at": datetime.utcnow()
                })
            elif data["action"] == "update":
                await self.db.structure_nodes.update_one(
                    {"reference_id": ObjectId(data["reference_id"])},
                    {
                        "$set": {
                            "name": data["name"],
                            "parent_id": ObjectId(data["parent_id"]),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            elif data["action"] == "delete":
                await self.db.structure_nodes.delete_one(
                    {"reference_id": ObjectId(data["reference_id"])}
                )
        except Exception as e:
            print(f"Error handling facility event: {e}")

    async def handle_ticket_event(self, data: dict):
        try:
            if data["action"] == "access_update":
                await self.db.access_control.update_one(
                    {"ticket_type_id": ObjectId(data["ticket_type_id"])},
                    {
                        "$set": {
                            "facility_ids": [ObjectId(fid) for fid in data["facility_ids"]],
                            "updated_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
        except Exception as e:
            print(f"Error handling ticket event: {e}")

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_client:
            await self.redis_client.close() 