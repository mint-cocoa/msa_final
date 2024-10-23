import os
from fastapi import FastAPI, HTTPException, Depends
from kafka import KafkaProducer
import json
from .dependencies import get_current_user
import aioredis
from .routes import router as ride_reservation_router

app = FastAPI(
    title="Ride Reservation Service",
    description="Service for managing ride reservations",
    version="1.0.0",
    root_path="/reservations"
)

KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092").split(",")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVERS,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.on_event("startup")
async def startup_event():
    app.state.redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ride Reservation Service"}

app.include_router(ride_reservation_router, prefix="/api")
