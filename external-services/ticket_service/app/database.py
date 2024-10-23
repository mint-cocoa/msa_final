# user_service/app/utils.py (유사하게 park_service 및 facility_service에도 생성)
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@mongodb:27017/tickets?authSource=admin")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



async def get_database(database_name):
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        await client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB: {database_name}")
        return client[database_name]
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def get_db(database_name):
    db = await get_database(database_name)
    try:
        yield db
    finally:
        logger.info("Closing database connection")
