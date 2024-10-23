from fastapi import FastAPI, WebSocket
from kafka import KafkaConsumer
import json
import asyncio

app = FastAPI()

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
    consumer = KafkaConsumer('real_time_updates',
                             bootstrap_servers=['kafka:9092'],
                             value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    for message in consumer:
        update = message.value
        for client in connected_clients:
            await client.send_json(update)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_updates())

@app.get("/")
async def root():
    return {"message": "Real-Time Tracking Service is running"}
