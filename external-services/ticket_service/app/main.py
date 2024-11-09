from fastapi import FastAPI
from .routes import router as ticket_router
from .publisher import EventPublisher
from .consumer import RabbitMQConsumer
import logging
import os
app = FastAPI(
    title="Ticket Service",
    description="Service for managing tickets",
    version="1.0.0",
    root_path="/tickets"
)

@app.on_event("startup")
async def startup_event():
    try:
        # RabbitMQ Publisher 설정
        app.state.publisher = EventPublisher()
        await app.state.publisher.connect()
        
        # RabbitMQ Consumer 설정
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        app.state.consumer = RabbitMQConsumer(rabbitmq_url=rabbitmq_url)
        await app.state.consumer.connect()
        
        logging.info("Successfully initialized RabbitMQ connections")
    except Exception as e:
        logging.error(f"Failed to initialize RabbitMQ connections: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        # RabbitMQ 연결 종료
        if hasattr(app.state, 'publisher'):
            await app.state.publisher.close()
        if hasattr(app.state, 'consumer'):
            await app.state.consumer.close()
        logging.info("Successfully closed RabbitMQ connections")
    except Exception as e:
        logging.error(f"Error closing RabbitMQ connections: {e}")

app.include_router(ticket_router, prefix="/api")