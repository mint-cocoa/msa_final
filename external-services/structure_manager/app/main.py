from fastapi import FastAPI
from .database import Database
from .consumer import RabbitMQConsumer
import os

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # RabbitMQ Consumer 설정
    app.state.consumer = RabbitMQConsumer()
    await app.state.consumer.connect()

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # RabbitMQ 연결 종료
    if hasattr(app.state, 'consumer'):
        await app.state.consumer.close()

# 헬스 체크를 위한 기본 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy"}