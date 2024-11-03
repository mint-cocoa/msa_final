# user_service/app/utils.py (유사하게 park_service 및 facility_service에도 생성)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging  
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@mongodb:27017/external?authSource=admin")
DATABASE_NAME = os.getenv("DATABASE_NAME", "external")

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        if cls.client is None:
            cls.client = AsyncIOMotorClient(
                MONGODB_URI,
                maxPoolSize=100,  # 연결 풀 크기 설정
                minPoolSize=20    # 최소 유지할 연결 수
            )
            logging.info("Created MongoDB connection pool")
    
    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            logging.info("Closed MongoDB connection pool")
            
            
async def get_db():
    if Database.client is None:
        await Database.connect_db()
    return Database.client[DATABASE_NAME]
    