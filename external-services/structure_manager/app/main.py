from fastapi import FastAPI
from .routes import router
from .database import Database
from .consumer import RedisConsumer
import asyncio
import os

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0",
    root_path="/structure"
)

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # Redis Consumer 설정
    app.state.consumer = RedisConsumer()
    
    # consumer 시작
    asyncio.create_task(app.state.consumer.start_consuming())

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # Redis 연결 종료
    await app.state.consumer.close()

app.include_router(router, prefix="/api")