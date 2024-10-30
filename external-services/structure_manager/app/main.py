from fastapi import FastAPI
import aio_pika
import os
from .routes import router
from .database import Database
from .consumer import start_consumer

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0",
    root_path="/structure"
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup_event():
    await Database.connect_db()
    # RabbitMQ 연결 설정
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_channel = await app.state.rabbitmq_connection.channel()
    # 컨슈머 시작
    asyncio.create_task(start_consumer(app.state.rabbitmq_channel))

@app.on_event("shutdown")
async def shutdown_event():
    await Database.close_db()
    await app.state.rabbitmq_connection.close()

app.include_router(router, prefix="/api") 