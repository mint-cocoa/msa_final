from fastapi import FastAPI, WebSocket
import aio_pika
import json
import asyncio
import os

app = FastAPI()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    finally:
        connected_clients.remove(websocket)

async def send_updates():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue('real_time_updates', durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                update = json.loads(message.body.decode())
                for client in connected_clients:
                    await client.send_json(update)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_updates())

@app.get("/")
async def root():
    return {"message": "Real-Time Tracking Service is running"}
