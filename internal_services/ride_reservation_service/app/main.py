import os
from fastapi import FastAPI
import aio_pika
from .routes import router as ride_reservation_router

app = FastAPI(
    title="Ride Reservation Service",
    description="Service for managing ride reservations",
    version="1.0.0",
    root_path="/reservations"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup_event():
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_channel = await app.state.rabbitmq_connection.channel()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.rabbitmq_connection.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ride Reservation Service"}

app.include_router(ride_reservation_router, prefix="/api")
