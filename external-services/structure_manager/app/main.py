from fastapi import FastAPI
from .database import Database
from .consumer import RabbitMQConsumer
from .publisher import EventPublisher
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0"
)

async def init_collections(db: AsyncIOMotorDatabase):
    try:
        # 현재 존재하는 컬렉션 목록 조회
        collections = await db.list_collection_names()
        
        # nodes 컬렉션 초기화
        if "nodes" not in collections:
            await db.create_collection("nodes")
            await db.nodes.create_index("reference_id", unique=True)
            await db.nodes.create_index("type")
            logging.info("Nodes collection initialized successfully")

        # parks 컬렉션 초기화
        if "parks" not in collections:
            await db.create_collection("parks")
            await db.parks.create_index("name", unique=True)
            logging.info("Parks collection initialized successfully")

        # facilities 컬렉션 초기화
        if "facilities" not in collections:
            await db.create_collection("facilities")
            await db.facilities.create_index("park_id")
            await db.facilities.create_index([("name", 1), ("park_id", 1)], unique=True)
            logging.info("Facilities collection initialized successfully")

    except Exception as e:
        logging.error(f"Failed to initialize collections: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    try:
        # 데이터베이스 연결 설정
        await Database.connect_db()
        db = Database.get_database()
        
        # 컬렉션 초기화
        await init_collections(db)
        
        # RabbitMQ Consumer 설정
        app.state.consumer = RabbitMQConsumer()
        await app.state.consumer.connect()
        
        # RabbitMQ Publisher 설정
        app.state.publisher = EventPublisher()
        await app.state.publisher.connect()
        
        logging.info("Application startup completed successfully")
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    await Database.close_db()
    if hasattr(app.state, 'consumer'):
        await app.state.consumer.close()
    if hasattr(app.state, 'publisher'):
        await app.state.publisher.close()
    logging.info("Application shutdown completed")