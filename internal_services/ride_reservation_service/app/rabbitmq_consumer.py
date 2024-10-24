import aio_pika
import json
import asyncio
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def process_message(message):
    async with message.process():
        reservation = json.loads(message.body.decode())
        print(f"Processing reservation: {reservation}")

async def start_consumer():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    queue = await channel.declare_queue("ride_reservations", durable=True)
    
    await queue.consume(process_message)
    
    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()

def run_consumer():
    asyncio.run(start_consumer())

if __name__ == "__main__":
    run_consumer()
