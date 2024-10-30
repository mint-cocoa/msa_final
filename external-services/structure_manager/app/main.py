from fastapi import FastAPI
import aio_pika
import os
from .routes import router
from .database import Database
from .consumer import StructureConsumer
import asyncio

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0",
    root_path="/structure"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # RabbitMQ 연결 및 consumer 설정
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.consumer = StructureConsumer(app.state.rabbitmq_connection)
    await app.state.consumer.setup()
    
    # consumer 시작
    asyncio.create_task(app.state.consumer.start_consuming())

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # RabbitMQ 연결 종료
    await app.state.consumer.close()
    await app.state.rabbitmq_connection.close()

app.include_router(router, prefix="/api")