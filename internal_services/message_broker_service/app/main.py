from fastapi import FastAPI, HTTPException
import aio_pika
import json
import asyncio
import os
from .redis_client import add_to_queue

app = FastAPI()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
connection = None
channel = None

async def get_channel():
    global connection, channel
    if not connection or connection.is_closed:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
    return channel

@app.post("/publish/{queue_name}")
async def publish_message(queue_name: str, message: dict):
    try:
        channel = await get_channel()
        await channel.declare_queue(queue_name, durable=True)
        
        message_body = json.dumps(message).encode()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key=queue_name
        )
        return {"status": "success", "queue": queue_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_message(message, queue_name):
    async with message.process():
        data = json.loads(message.body.decode())
        if queue_name == 'facility_queue':
            await process_facility_queue(data)
        elif queue_name == 'ride_reservations':
            await process_ride_reservation(data)
        elif queue_name == 'notifications':
            await process_notification(data)
        elif queue_name == 'real_time_updates':
            await process_real_time_update(data)
        elif queue_name == 'exit_park':
            await process_exit_park(data)

async def setup_consumer():
    channel = await get_channel()
    queues = ['ride_reservations', 'notifications', 'real_time_updates', 
              'exit_park', 'facility_queue']
    
    for queue_name in queues:
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(lambda m: process_message(m, queue_name))

@app.on_event("startup")
async def startup_event():
    await setup_consumer()

@app.on_event("shutdown")
async def shutdown_event():
    if connection and not connection.is_closed:
        await connection.close()

async def process_facility_queue(data):
    facility_id = data['facility_id']
    user_id = data['user_id']
    await add_to_queue(facility_id, user_id)
    print(f"User {user_id} added to facility {facility_id} queue.")

async def process_ride_reservation(data):
    print(f"Processing ride reservation: {data}")

async def process_notification(data):
    print(f"Processing notification: {data}")

async def process_real_time_update(data):
    print(f"Processing real-time update: {data}")

async def process_exit_park(data):
    print(f"Processing park exit: {data}")
