from bson import ObjectId
from .models import FacilityCreate, FacilityUpdate
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

async def create_facility(db: AsyncIOMotorDatabase, facility: FacilityCreate):
    facility_data = facility.dict()
    facility_data["created_at"] = datetime.utcnow()
    facility_data["updated_at"] = datetime.utcnow()
    
    result = await db.facilities.insert_one(facility_data)
    return str(result.inserted_id)

async def update_facility(db: AsyncIOMotorDatabase, facility_id: str, facility: FacilityUpdate):
    facility_data = facility.dict(exclude_unset=True)
    facility_data["updated_at"] = datetime.utcnow()
    
    result = await db.facilities.update_one(
        {"_id": ObjectId(facility_id)},
        {"$set": facility_data}
    )
    return result.modified_count > 0

async def delete_facility(db: AsyncIOMotorDatabase, facility_id: str):
    result = await db.facilities.delete_one({"_id": ObjectId(facility_id)})
    return result.deleted_count > 0

async def get_facility(db: AsyncIOMotorDatabase, facility_id: str):
    facility = await db.facilities.find_one({"_id": ObjectId(facility_id)})
    return facility

async def get_facilities(db: AsyncIOMotorDatabase, park_id: str = None, skip: int = 0, limit: int = 10):
    filter_query = {"park_id": ObjectId(park_id)} if park_id else {}
    cursor = db.facilities.find(filter_query).skip(skip).limit(limit)
    return await cursor.to_list(length=limit) 