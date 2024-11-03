from fastapi import FastAPI
import redis.asyncio as redis
import json
from .operations import process_notification
import asyncio
import os

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

async def consume_messages():
    redis_client = await redis.from_url(REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                notification = json.loads(message["data"])
                await process_notification(notification)
    finally:
        await pubsub.unsubscribe("notifications")
        await redis_client.close()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}
