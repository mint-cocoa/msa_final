from fastapi import FastAPI
from .database import Database, get_db
from .consumer import RabbitMQConsumer
from .publisher import EventPublisher
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from .routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0",
    root_path="/structure"
)

async def init_structure_collections(db: AsyncIOMotorDatabase):
    try:
        collections = await db.list_collection_names()
        
        if "nodes" not in collections:
            await db.create_collection("nodes")
            await db.nodes.create_index("reference_id", unique=True)
            await db.nodes.create_index("type")
            logging.info("Nodes collection initialized successfully")
            
    except Exception as e:
        logging.error(f"Failed to initialize structure collections: {e}")
        raise

async def init_park_collections(db: AsyncIOMotorDatabase):
    try:
        collections = await db.list_collection_names()
        
        if "parks" not in collections:
            await db.create_collection("parks")
            await db.parks.create_index("name", unique=True)
            logging.info("Parks collection initialized successfully")
            
    except Exception as e:
        logging.error(f"Failed to initialize park collections: {e}")
        raise

async def init_facility_collections(db: AsyncIOMotorDatabase):
    try:
        collections = await db.list_collection_names()
        
        if "facilities" not in collections:
            await db.create_collection("facilities")
            await db.facilities.create_index("park_id")
            await db.facilities.create_index([("name", 1), ("park_id", 1)], unique=True)
            logging.info("Facilities collection initialized successfully")
            
    except Exception as e:
        logging.error(f"Failed to initialize facility collections: {e}")
        raise

async def init_ticket_collections(db: AsyncIOMotorDatabase):
    try:
        collections = await db.list_collection_names()
        
        if "tickets" not in collections:
            await db.create_collection("tickets")
            await db.tickets.create_index("park_id")
            await db.tickets.create_index("user_id")
            logging.info("Tickets collection initialized successfully")
            
    except Exception as e:
        logging.error(f"Failed to initialize ticket collections: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    try:
        # 데이터베이스 연결 및 초기화
        await Database.connect_db()
        
        # 각 서비스별 DB 초기화
        structure_db = Database.get_database('structure')
        park_db = Database.get_database('park')
        facility_db = Database.get_database('facility')
        ticket_db = Database.get_database('ticket')
        
        await init_structure_collections(structure_db)
        await init_park_collections(park_db)
        await init_facility_collections(facility_db)
        await init_ticket_collections(ticket_db)
        
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
    
app.include_router(router, prefix="/api")