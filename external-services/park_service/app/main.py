# park_service/app/main.py
from fastapi import FastAPI
from .routes import router
from .publisher import EventPublisher

app = FastAPI(
    title="Park Service",
    description="Service for managing theme parks",
    version="1.0.0",
    root_path="/parks"
)

@app.on_event("startup")
async def startup_event():
    # RabbitMQ Publisher 설정
    app.state.publisher = EventPublisher()
    await app.state.publisher.connect()

@app.on_event("shutdown")
async def shutdown_event():
    # RabbitMQ 연결 종료
    if hasattr(app.state, 'publisher'):
        await app.state.publisher.close()

app.include_router(router, prefix="/api")