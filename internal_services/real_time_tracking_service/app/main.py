from fastapi import FastAPI, WebSocket
import redis.asyncio as redis
import json
import asyncio
import os

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

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
    redis_client = await redis.from_url(REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("real_time_updates")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                update = json.loads(message["data"])
                for client in connected_clients:
                    await client.send_json(update)
    finally:
        await pubsub.unsubscribe("real_time_updates")
        await redis_client.close()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_updates())

@app.get("/")
async def root():
    return {"message": "Real-Time Tracking Service is running"}
