# user_service/app/utils.py (유사하게 park_service 및 facility_service에도 생성)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging  
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@mongodb:27017/facilities?authSource=admin")
DATABASE_NAME = os.getenv("DATABASE_NAME", "facilities")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_database():
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        await client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB: {DATABASE_NAME}")
        return client[DATABASE_NAME]
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def get_db():
    db = await get_database()  # 데이터베이스 연결 객체를 가져옴
    try:
        yield db 
    finally:
        pass
    