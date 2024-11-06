from motor.motor_asyncio import AsyncIOMotorClient
import os

class Database:
    client: AsyncIOMotorClient = None
    database_name = os.getenv("DATABASE_NAME", "structure")

    @classmethod
    async def connect_db(cls):
        cls.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        
    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_database(cls):
        return cls.client[cls.database_name]

async def get_db():
    db = Database.get_database()
    return db 