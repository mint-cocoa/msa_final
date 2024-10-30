# facility_service/app/main.py
from fastapi import FastAPI
import aio_pika
import os
from .routes import router
from .database import Database
from .rabbitmq import RabbitMQPublisher

app = FastAPI(
    title="Facility Service",
    description="Service for managing theme park facilities",
    version="1.0.0",
    root_path="/facilities"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # RabbitMQ 연결 설정
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_publisher = RabbitMQPublisher(app.state.rabbitmq_connection)

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # RabbitMQ 연결 종료
    await app.state.rabbitmq_publisher.close()
    await app.state.rabbitmq_connection.close()

app.include_router(router, prefix="/api")