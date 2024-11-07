# facility_service/app/main.py
from fastapi import FastAPI
from .routes import router
from .publisher import EventPublisher
from .consumer import RabbitMQConsumer

app = FastAPI(
    title="Facility Service",
    description="Service for managing theme park facilities",
    version="1.0.0",
    root_path="/facilities"
)

@app.on_event("startup")
async def startup_event():
    # RabbitMQ Publisher 설정
    app.state.publisher = EventPublisher()
    await app.state.publisher.connect()
    
    # RabbitMQ Consumer 설정
    app.state.consumer = RabbitMQConsumer()
    await app.state.consumer.connect()

@app.on_event("shutdown")
async def shutdown_event():
    # RabbitMQ 연결 종료
    if hasattr(app.state, 'publisher'):
        await app.state.publisher.close()
    if hasattr(app.state, 'consumer'):
        await app.state.consumer.close()

app.include_router(router, prefix="/api")