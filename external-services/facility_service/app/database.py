# user_service/app/utils.py (유사하게 park_service 및 facility_service에도 생성)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mydatabase")

def get_database():
    client = AsyncIOMotorClient(MONGODB_URI)
    return client[DATABASE_NAME]
