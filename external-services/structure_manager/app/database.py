from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    database_name = os.getenv("DATABASE_NAME", "structure")

    @classmethod
    async def connect_db(cls):
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            cls.client = AsyncIOMotorClient(mongodb_uri)
            cls.db = cls.client[cls.database_name]
            
            # 연결 테스트
            await cls.db.command("ping")
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
        
    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            logging.info("MongoDB connection closed")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise Exception("Database not initialized. Call connect_db() first.")
        return cls.db

async def get_db() -> AsyncIOMotorDatabase:
    if Database.db is None:
        await Database.connect_db()
    return Database.get_database()