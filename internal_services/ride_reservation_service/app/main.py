import os
from fastapi import FastAPI
import aio_pika
from .routes import router as ride_reservation_router
from .database import Database
from .rabbitmq import RabbitMQPublisher

app = FastAPI(
    title="Ride Reservation Service",
    description="Service for managing ride reservations",
    version="1.0.0",
    root_path="/reservations"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # RabbitMQ 연결 설정
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_publisher = RabbitMQPublisher(app.state.rabbitmq_connection)
    
    # Redis 연결 설정 (이미 있는 경우)
    app.state.redis = await aioredis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379"),
        encoding="utf-8",
        decode_responses=True
    )

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # RabbitMQ 연결 종료
    await app.state.rabbitmq_publisher.close()
    await app.state.rabbitmq_connection.close()
    
    # Redis 연결 종료 (이미 있는 경우)
    await app.state.redis.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ride Reservation Service"}

app.include_router(ride_reservation_router, prefix="/api")
