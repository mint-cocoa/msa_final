from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
from typing import Dict

class Database:
    clients: Dict[str, AsyncIOMotorClient] = {}
    dbs: Dict[str, AsyncIOMotorDatabase] = {}
    
    service_configs = {
        "structure": {
            "uri": "mongodb://root:example@mongodb-structure:27017/structure?authSource=admin",
            "db_name": "structure"
        },
        "park": {
            "uri": "mongodb://root:example@mongodb-park:27017/parks?authSource=admin",
            "db_name": "parks"
        },
        "facility": {
            "uri": "mongodb://root:example@mongodb-facility:27017/facilities?authSource=admin",
            "db_name": "facilities"
        },
        "ticket": {
            "uri": "mongodb://root:example@mongodb-ticket:27017/tickets?authSource=admin",
            "db_name": "tickets"
        }
    }

    @classmethod
    async def connect_db(cls):
        try:
            for service, config in cls.service_configs.items():
                cls.clients[service] = AsyncIOMotorClient(config["uri"])
                cls.dbs[service] = cls.clients[service][config["db_name"]]
                
                # 연결 테스트
                await cls.dbs[service].command("ping")
                logging.info(f"Successfully connected to MongoDB {service} Database")
                
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
        
    @classmethod
    async def close_db(cls):
        for service, client in cls.clients.items():
            if client is not None:
                client.close()
                logging.info(f"MongoDB {service} connection closed")

    @classmethod
    def get_database(cls, service: str = "structure") -> AsyncIOMotorDatabase:
        if service not in cls.dbs or cls.dbs[service] is None:
            raise Exception(f"Database {service} not initialized. Call connect_db() first.")
        return cls.dbs[service]

async def get_db(service: str = "structure") -> AsyncIOMotorDatabase:
    if not Database.dbs:
        await Database.connect_db()
    return Database.get_database(service)