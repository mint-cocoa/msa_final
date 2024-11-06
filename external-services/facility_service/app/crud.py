from bson import ObjectId
from .models import FacilityModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import redis.asyncio as redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL)
    return redis_client

async def create_facility(db: AsyncIOMotorDatabase, facility: FacilityModel):
    try:
        # MongoDB에 시설 데이터 저장
        facility_data = facility.dict()
        facility_data["created_at"] = datetime.utcnow()
        facility_data["updated_at"] = datetime.utcnow()
        
        result = await db.facilities.insert_one(facility_data)
        facility_id = str(result.inserted_id)

        # Redis에 이벤트 발행
        redis = await get_redis()
        event_data = {
            "action": "facility_create",
            "reference_id": facility_id,
            "name": facility.name,
            "parent_id": str(facility.park_id)
        }
        await redis.publish('facility_create', json.dumps(event_data))
        
        return facility_id
    except Exception as e:
        print(f"Error creating facility: {e}")
        raise

async def update_facility(db: AsyncIOMotorDatabase, facility_id: str, facility: FacilityModel):
    try:
        facility_data = facility.dict(exclude_unset=True)
        facility_data["updated_at"] = datetime.utcnow()
        
        result = await db.facilities.update_one(
            {"_id": ObjectId(facility_id)},
            {"$set": facility_data}
        )

        if result.modified_count > 0:
            redis = await get_redis()
            event_data = {
                "action": "facility_update",
                "reference_id": facility_id,
                "name": facility.name,
                "parent_id": str(facility.park_id)
            }
            await redis.publish('facility_update', json.dumps(event_data))
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating facility: {e}")
        raise

async def delete_facility(db: AsyncIOMotorDatabase, facility_id: str):
    try:
        result = await db.facilities.delete_one({"_id": ObjectId(facility_id)})
        
        if result.deleted_count > 0:
            redis = await get_redis()
            event_data = {
                "action": "facility_delete",
                "reference_id": facility_id
            }
            await redis.publish('facility_delete', json.dumps(event_data))
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting facility: {e}")
        raise

async def get_facility(db: AsyncIOMotorDatabase, facility_id: str):
    try:
        facility = await db.facilities.find_one({"_id": ObjectId(facility_id)})
        return facility
    except Exception as e:
        print(f"Error getting facility: {e}")
        raise

async def get_facilities(db: AsyncIOMotorDatabase, park_id: str = None, skip: int = 0, limit: int = 10):
    try:
        filter_query = {"park_id": ObjectId(park_id)} if park_id else {}
        cursor = db.facilities.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    except Exception as e:
        print(f"Error getting facilities: {e}")
        raise



async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None