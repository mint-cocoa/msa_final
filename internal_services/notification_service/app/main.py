from fastapi import FastAPI
import aio_pika
import json
from .operations import process_notification
import asyncio
import os

app = FastAPI()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def consume_messages():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue('notifications', durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                notification = json.loads(message.body.decode())
                await process_notification(notification)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}
