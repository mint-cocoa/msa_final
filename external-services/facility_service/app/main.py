# facility_service/app/main.py
from fastapi import FastAPI
from .routes import router
from .database import Database
from common.publisher import RedisPublisher

app = FastAPI(
    title="Facility Service",
    description="Service for managing theme park facilities",
    version="1.0.0",
    root_path="/facilities"
)

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 연결 설정
    await Database.connect_db()
    
    # Redis Publisher 설정
    app.state.publisher = RedisPublisher()
    await app.state.publisher.connect()

@app.on_event("shutdown")
async def shutdown_event():
    # 데이터베이스 연결 종료
    await Database.close_db()
    
    # Redis 연결 종료
    await app.state.publisher.close()

app.include_router(router, prefix="/api")