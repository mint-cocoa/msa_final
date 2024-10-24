import os
from fastapi import FastAPI
import aio_pika
import aioredis
from .routes import router as ride_reservation_router

app = FastAPI(
    title="Ride Reservation Service",
    description="Service for managing ride reservations",
    version="1.0.0",
    root_path="/reservations"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@app.on_event("startup")
async def startup_event():
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_channel = await app.state.rabbitmq_connection.channel()
    app.state.redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.rabbitmq_connection.close()
    await app.state.redis.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ride Reservation Service"}

app.include_router(ride_reservation_router, prefix="/api")
