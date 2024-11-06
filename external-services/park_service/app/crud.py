from bson import ObjectId
from .models import ParkModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

async def create_park(db: AsyncIOMotorDatabase, park: ParkModel):
    park_data = park.dict()
    park_data["created_at"] = datetime.utcnow()
    park_data["updated_at"] = datetime.utcnow()
    
    result = await db.parks.insert_one(park_data)
    return str(result.inserted_id)

async def update_park(db: AsyncIOMotorDatabase, park_id: str, park: ParkModel):
    park_data = park.dict(exclude_unset=True)
    park_data["updated_at"] = datetime.utcnow()
    
    result = await db.parks.update_one(
        {"_id": ObjectId(park_id)},
        {"$set": park_data}
    )
    return result.modified_count > 0

async def delete_park(db: AsyncIOMotorDatabase, park_id: str):
    result = await db.parks.delete_one({"_id": ObjectId(park_id)})
    return result.deleted_count > 0

async def get_park(db: AsyncIOMotorDatabase, park_id: str):
    park = await db.parks.find_one({"_id": ObjectId(park_id)})
    return park

async def get_parks(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 10):
    cursor = db.parks.find().skip(skip).limit(limit)
    return await cursor.to_list(length=limit) 