# user_service/app/utils.py (유사하게 park_service 및 facility_service에도 생성)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@mongodb:27017/users?authSource=admin")
DATABASE_NAME = os.getenv("DATABASE_NAME", "users")

async def get_database():
    client = AsyncIOMotorClient(MONGODB_URI)
    return client[DATABASE_NAME]


async def get_db():
    db = await get_database()  # 데이터베이스 연결 객체를 가져옴
    try:
        yield db 
    finally:
        pass
    